import logging

from django.contrib import messages

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import logout
from django.views.decorators.http import require_http_methods
from .models import TimeEntry, CustomUser, Station, Zeitarbeitsfirma, Notification
from .forms import AdminCreationForm, ProjectManagerCreationForm, TempWorkerCreationForm, StationCreationForm, TempFirmCreationForm, generate_password
from django.shortcuts import render , redirect

from django.urls import reverse, reverse_lazy

from django.http import JsonResponse
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .forms import generate_password

from django.views.generic import ListView
from django.db.models import Sum, F
from datetime import timedelta
from django.db.models import Count
import pandas as pd
from io import BytesIO
import xlsxwriter
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import JSONParser

import json
from django.middleware.csrf import get_token
logger = logging.getLogger(__name__)


class AdminDashboard(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = TimeEntry
    template_name = 'time_tracking/admin/admin_dashboard.html'
    context_object_name = 'time_entries'
    login_url = 'login'

    def test_func(self):
        return self.request.user.user_type == 'ADMIN'
    
    def get_queryset(self):
        # Group entries by worker and date
        return TimeEntry.objects.select_related(
            'user', 
            'user__station', 
            'user__project_manager',
            'user__zeitarbeitsfirma'
        ).order_by('user', '-timestamp')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Basic statistics and filter options
        context['active_users_count'] = CustomUser.objects.filter(is_active=True).count()
        context['stations'] = Station.objects.all()
        context['companies'] = Zeitarbeitsfirma.objects.all()
        context['project_managers'] = CustomUser.objects.filter(user_type='PROJECT_MANAGER')
        context['user_types'] = [
            ('ALL', 'Alle Benutzer'),
            ('TEMP_WORKER', 'Zeitarbeitskräfte'),
            ('PROJECT_MANAGER', 'Projektleiter')
        ]
        
        # Get all users for the user table
        context['users'] = CustomUser.objects.select_related(
            'station', 
            'project_manager',
            'zeitarbeitsfirma'
        ).filter(
            is_superuser=False
        ).order_by('user_type', 'last_name', 'first_name')

        # Initialize workers_data dictionary
        workers_data = {}
        
        # Process time entries
        for entry in self.get_queryset():
            worker = entry.user
            date = entry.timestamp.date()
            
            # Initialize worker and date if not exists
            if worker not in workers_data:
                workers_data[worker] = {}
            if date not in workers_data[worker]:
                workers_data[worker][date] = {
                    'entries': [],
                    'total_work': timedelta(),
                    'total_break': timedelta(),
                    'notes': []
                }
            
            # Add entry to list
            workers_data[worker][date]['entries'].append(entry)
            
            # Calculate times only if we have at least 2 entries
            entries = workers_data[worker][date]['entries']
            if len(entries) >= 2:
                last_entry = entries[-1]
                prev_entry = entries[-2]
                
                # Calculate work time
                if last_entry.entry_type == 'GEHEN' and prev_entry.entry_type == 'KOMMEN':
                    work_time = last_entry.timestamp - prev_entry.timestamp
                    workers_data[worker][date]['total_work'] += work_time
                
                # Calculate break time
                if last_entry.entry_type == 'KOMMEN' and prev_entry.entry_type == 'GEHEN':
                    break_time = last_entry.timestamp - prev_entry.timestamp
                    workers_data[worker][date]['total_break'] += break_time
            
            # Add notes
            if entry.note:
                workers_data[worker][date]['notes'].append(entry.note)
        
        context['workers_data'] = workers_data
        return context

class CustomLoginView(LoginView):
    template_name = 'time_tracking/login.html'
    
    def form_valid(self, form):
        """Log successful logins"""
        response = super().form_valid(form)
        logger.info(f"Successful login for user: {self.request.user} (type: {self.request.user.user_type})")
        return response

    def form_invalid(self, form):
        """Log failed login attempts"""
        logger.warning(f"Failed login attempt: {form.errors}")
        messages.error(self.request, 'Ungültige Anmeldedaten. Bitte versuchen Sie es erneut.')
        return super().form_invalid(form)
    
    def get_success_url(self):
        """Return the URL to redirect to after successful login"""
        user = self.request.user
        try:
            if user.user_type == 'ADMIN':
                return reverse('admin-dashboard')
            elif user.user_type == 'PROJECT_MANAGER':
                return reverse('project_manager_dashboard')
            else:
                return reverse('time-tracking')
        except Exception as e:
            logger.error(f"Error in get_success_url for user {user}: {str(e)}")
            return reverse('login')
        
class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('login')
    
    def dispatch(self, request, *args, **kwargs):
        # Clear all session data
        request.session.flush()
        # Perform logout
        logout(request)
        # Redirect to login page
        return super().dispatch(request, *args, **kwargs)


# Create your views here.
def is_admin(user):
    return user.user_type == 'ADMIN'

def is_project_manager(user):
    return user.user_type == 'PROJECT_MANAGER'

class ProjectManagerDashboard(UserPassesTestMixin, ListView):
    model = TimeEntry
    template_name = 'time_tracking/admin/project_manager_dashboard.html'
    context_object_name = 'time_entries'
    paginate_by = 10
    ordering = ['-timestamp']

    def test_func(self):
        return is_project_manager(self.request.user)

    def get_queryset(self):
        return TimeEntry.objects.filter(
            user__project_manager=self.request.user
        ).select_related('user')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Mitarbeiter des Projektleiters
        context['workers'] = CustomUser.objects.filter(
            project_manager=self.request.user,
            user_type='TEMP_WORKER'
        )
        context['active_workers_count'] = context['workers'].filter(is_active=True).count()
        
        # Change status to approval_status
        context['pending_entries'] = TimeEntry.objects.filter(
            user__project_manager=self.request.user,
            approval_status='PENDING'  # Changed from status to approval_status
        ).select_related('user').order_by('-timestamp')
        
        context['notifications'] = Notification.objects.filter(
            user=self.request.user,
            read=False
        ).order_by('-created_at')
        return context
    
@user_passes_test(lambda u: u.user_type == 'ADMIN')
def create_admin(request):
    storage = messages.get_messages(request)
    storage.used = True

    if request.method == 'POST':
        form = AdminCreationForm(request.POST)
        if form.is_valid():
            result = form.save()  # Get dictionary with user and password
            user = result['user']  # Extract user from dictionary
            messages.success(request, 
                f'Admin-Account wurde erfolgreich erstellt.\nZugangsdaten wurden per E-Mail an {user.email} gesendet.')
            return redirect('admin-dashboard')
    else:
        initial_password = generate_password()
        form = AdminCreationForm(initial={'generated_password': initial_password})
    
    return render(request, 'time_tracking/admin/create-admin/create_admin.html', {
        'form': form,
        'initial_password': form.initial.get('generated_password', '')
    })

@user_passes_test(lambda u: u.user_type == 'ADMIN')
def create_temp_worker(request):
    #Clear any existing messages at the start
    storage = messages.get_messages(request)
    storage.used = True

    if request.method == 'POST':
        form = TempWorkerCreationForm(request.POST)
        if form.is_valid():
            password = request.session.get('temp_password')
            if not password:
                messages.error(request, 'Password generation error. Please try again.')
                return redirect('create-temp-worker')
            
            user = form.save(commit=False)
            user.set_password(password)
            user.save()
            
            # Send welcome email with credentials
            try:
                form.send_credentials_email(user, password)
                messages.success(request, 
                    f'Zeitarbeitskraft-Account wurde erfolgreich erstellt.\nZugangsdaten wurden per E-Mail an {user.email} gesendet.')
            except Exception as e:
                messages.warning(request, 
                    f'Account erstellt, aber E-Mail konnte nicht gesendet werden: {str(e)}')
            
            # Clear the temporary password
            if 'temp_password' in request.session:
                del request.session['temp_password']
                
            return redirect('admin-dashboard')
    else:
        form = TempWorkerCreationForm()
        initial_password = generate_password()
        request.session['temp_password'] = initial_password
    
    return render(request, 'time_tracking/admin/temp-worker/create_temp_worker.html', {
        'form': form,
        'initial_password': initial_password
    })

@user_passes_test(lambda u: u.user_type == 'ADMIN')
def create_project_manager(request):
    #Clear any existing messages at the start
    storage = messages.get_messages(request)
    storage.used = True
    if request.method == 'POST':
        form = ProjectManagerCreationForm(request.POST)
        if form.is_valid():
            password = request.session.get('temp_password')
            if not password:
                messages.error(request, 'Password generation error. Please try again.')
                return redirect('create-project-manager')
            
            user = form.save(commit=False)
            user.set_password(password)
            user.save()
            
            # Send welcome email with credentials
            try:
                form.send_credentials_email(user, password)
                messages.success(request, 
                    f'Projektleiter-Account wurde erfolgreich erstellt.\nZugangsdaten wurden per E-Mail an {user.email} gesendet.')
            except Exception as e:
                messages.warning(request, 
                    f'Account erstellt, aber E-Mail konnte nicht gesendet werden: {str(e)}')
            
            # Clear the temporary password
            if 'temp_password' in request.session:
                del request.session['temp_password']
                
            return redirect('admin-dashboard')
    else:
        form = ProjectManagerCreationForm()
        initial_password = generate_password()
        request.session['temp_password'] = initial_password
    
    return render(request, 'time_tracking/admin/project-manager/create_project_manager.html', {
        'form': form,
        'initial_password': initial_password
    })
       

@user_passes_test(lambda u: u.user_type == 'ADMIN')
def create_temp_firm(request):
    if request.method == 'POST':
        form = TempFirmCreationForm(request.POST)
        if form.is_valid():
            temp_firm = form.save()
            messages.success(request, f'Temporary firm {temp_firm.name} created successfully.')
            return redirect('admin-dashboard')
    else:
        form = TempFirmCreationForm()
    return render(request, 'time_tracking/admin/temp-firm/create_temp_firm.html', {'form': form})

@user_passes_test(lambda u: u.user_type == 'ADMIN')
def create_station(request):
    if request.method == 'POST':
        form = StationCreationForm(request.POST)
        if form.is_valid():
            station = form.save()
            messages.success(request, f'Station {station.name} at {station.location} created successfully.')
            return redirect('admin-dashboard')
    else:
        form = StationCreationForm()  # Initialize form for GET request
        
    return render(request, 'time_tracking/admin/station/create_station.html', {'form': form})

@login_required
def time_tracking_view(request):
    if request.user.user_type != 'TEMP_WORKER':
        return redirect('login')  # Redirect to login if not TEMP_WORKER
        
    # Get today's entries
    today = timezone.now().date()
    time_entries = TimeEntry.objects.filter(
        user=request.user,
        timestamp__date=today
    ).order_by('-timestamp')
    
    # Get last action
    last_entry = time_entries.first()
    last_action = last_entry.entry_type.lower() if last_entry else None
    
    # Show Feierabend button only after GEHEN
    show_feierabend = last_action == 'gehen'
    
    return render(request, 'time_tracking/tracking.html', {
        'time_entries': time_entries,
        'last_action': last_action,
        'show_feierabend': show_feierabend
    })

    
@api_view(['POST'])
def toggle_worker_status(request, worker_id):
    try:
        worker = CustomUser.objects.get(
            id=worker_id, 
            project_manager=request.user,
            user_type='TEMP_WORKER'
        )
        worker.is_active = not worker.is_active
        worker.save()
        return Response({'status': 'success', 'is_active': worker.is_active})
    except CustomUser.DoesNotExist:
        return Response({'status': 'error'}, status=404)
    
@api_view(['POST'])
def approve_time_entry(request, entry_id):
    try:
        entry = TimeEntry.objects.get(
            id=entry_id,
            user__project_manager=request.user
        )
        
        # Only allow manager notes for Feierabend entries
        if entry.entry_type == 'FEIERABEND':
            entry.manager_note = request.data.get('manager_note', '')
        
        entry.approval_status = 'APPROVED'
        entry.approved_at = timezone.now()
        entry.approved_by = request.user
        entry.save()
        
        # Create notification for admin
        Notification.objects.create(
            user=CustomUser.objects.filter(user_type='ADMIN').first(),
            title='Neue bestätigte Zeiterfassung',
            message=f'Zeiterfassung von {entry.user.get_full_name()} wurde bestätigt',
            entry=entry
        )
        
        return Response({'status': 'success'})
    except TimeEntry.DoesNotExist:
        return Response({'status': 'error', 'message': 'Zeiteintrag nicht gefunden'}, status=404)
    except Exception as e:
        return Response({'status': 'error', 'message': str(e)}, status=400)


def redirect_to_appropriate_page(request):
    if request.user.is_authenticated:
        if request.user.user_type == 'ADMIN':
            return redirect('admin-dashboard')
        elif request.user.user_type == 'PROJECT_MANAGER':
            return redirect('project_manager_dashboard')
        else:
            return redirect('time-tracking')
    return redirect('login')

def get_user_time_entries(request, user_id):
    user = CustomUser.objects.get(id=user_id)
    entries = TimeEntry.objects.filter(user=user).order_by('timestamp')
    
    # Group entries by date
    entries_by_date = {}
    for entry in entries:
        date = entry.timestamp.date()
        if date not in entries_by_date:
            entries_by_date[date] = {
                'date': date.strftime('%Y-%m-%d'),
                'last_name': user.last_name,
                'first_name': user.first_name,
                'start_time': None,
                'end_time': None,
                'break_duration': '00:00',
                'worker_note': '',
                'manager_note': '',
                'status': 'Offen'
            }
        
        if entry.entry_type == 'KOMMEN' and not entries_by_date[date]['start_time']:
            entries_by_date[date]['start_time'] = entry.timestamp.strftime('%H:%M')
        elif entry.entry_type == 'GEHEN':
            entries_by_date[date]['end_time'] = entry.timestamp.strftime('%H:%M')
    
    return JsonResponse(list(entries_by_date.values()), safe=False)

def export_time_entries(request):
    user_ids = request.POST.getlist('user_ids[]')
    users = CustomUser.objects.filter(id__in=user_ids, user_type='TEMP_WORKER')
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for user in users:
            entries = TimeEntry.objects.filter(user=user).order_by('timestamp')
            data = []
            
            # Convert entries to pandas DataFrame
            for entry in entries:
                data.append({
                    'Datum': entry.timestamp.date(),
                    'Nachname': user.last_name,
                    'Vorname': user.first_name,
                    'Arbeitsbeginn': entry.timestamp.strftime('%H:%M') if entry.entry_type == 'KOMMEN' else '',
                    'Arbeitsende': entry.timestamp.strftime('%H:%M') if entry.entry_type == 'GEHEN' else '',
                    'Pause': '00:00',  # Calculate actual break time
                    'Notiz Zeitarbeitskraft': entry.note or '',
                    'Notiz Projektleiter': ''  # Add manager note field to model
                })
            
            df = pd.DataFrame(data)
            df.to_excel(writer, sheet_name=f"{user.username}", index=False)
    
    output.seek(0)
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=zeiterfassung.xlsx'
    return response

@require_http_methods(["POST"])
@login_required
def create_time_entry(request):
    # Logge die grundlegenden Informationen zum Nutzer
    logger.debug(f"User: {request.user}, User Type: {getattr(request.user, 'user_type', 'unbekannt')}")

    logger.debug(f"create_time_entry called. User: {request.user}, "
                 f"User Type: {getattr(request.user, 'user_type', 'unbekannt')}, "
                 f"Authenticated: {request.user.is_authenticated}")

    # Überprüfe, ob der angemeldete Nutzer tatsächlich ein TEMP_WORKER ist
    if request.user.user_type != 'TEMP_WORKER':
        logger.debug("User is not a TEMP_WORKER. Redirecting to tracking view.")
        # Redirect anstatt JSON-Response, falls der Nutzer nicht berechtigt ist
        return redirect('tracking')

    # Überprüfe den X-Requested-With Header
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        logger.error("Missing or incorrect X-Requested-With header.")
        return JsonResponse({
            'status': 'error',
            'message': 'AJAX request required'
        }, status=400)

    try:
        # Versuche, den Request-Body als JSON zu laden
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            logger.error("Invalid JSON data received.")
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data'
            }, status=400)

        entry_type = data.get('type', '').upper()
        if entry_type not in ['KOMMEN', 'GEHEN', 'FEIERABEND']:
            logger.error(f"Invalid entry type received: {entry_type}")
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid entry type'
            }, status=400)

        # Erstelle den Zeiteintrag
        entry = TimeEntry.objects.create(
            user=request.user,
            entry_type=entry_type,
            note=data.get('note'),
            timestamp=timezone.now()
        )

        if entry_type == 'FEIERABEND' and request.user.project_manager:
            notify_project_manager(entry)

        response_data = {
            'status': 'success',
            'data': {
                'id': entry.id,
                'timestamp': entry.timestamp.isoformat(),
                'type': entry_type,
                'note': entry.note or ''
            }
        }
        logger.debug(f"Time entry created successfully: {response_data}")
        return JsonResponse(response_data, status=201)

    except Exception as e:
        logger.error(f"Error creating time entry: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

def notify_project_manager(entry):
    # Add notification for project manager
    Notification.objects.create(
        user=entry.user.project_manager,
        title='Neue Zeiterfassung zur Überprüfung',
        message=f'Zeiterfassung von {entry.user.get_full_name()} vom {entry.timestamp.date()}',
        entry=entry
    )

@api_view(['GET', 'PUT'])
def edit_user(request, user_id):
    try:
        user = CustomUser.objects.get(id=user_id)
        
        if request.method == 'GET':
            return JsonResponse({
                'id': user.id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'user_type': user.user_type,
                'station': user.station.id if user.station else None,
                'project_manager': user.project_manager.id if user.project_manager else None,
                'zeitarbeitsfirma': user.zeitarbeitsfirma.id if user.zeitarbeitsfirma else None,
                'is_active': user.is_active
            })
        
        elif request.method == 'PUT':
            # Update user data
            data = json.loads(request.body)
            user.first_name = data.get('first_name', user.first_name)
            user.last_name = data.get('last_name', user.last_name)
            user.email = data.get('email', user.email)
            user.is_active = data.get('is_active', user.is_active)
            
            if 'station' in data and data['station']:
                user.station_id = data['station']
            if 'project_manager' in data and data['project_manager']:
                user.project_manager_id = data['project_manager']
            if 'zeitarbeitsfirma' in data and data['zeitarbeitsfirma']:
                user.zeitarbeitsfirma_id = data['zeitarbeitsfirma']
                
            user.save()
            return JsonResponse({'status': 'success'})
            
    except CustomUser.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@api_view(['DELETE'])
def delete_user(request, user_id):
    try:
        user = CustomUser.objects.get(id=user_id)
        user.delete()
        return JsonResponse({'status': 'success'})
    except CustomUser.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def imprint(request):
    return render(request, 'time_tracking/legal/imprint.html')

def privacy_policy(request):
    return render(request, 'time_tracking/legal/privacy_policy.html')


@user_passes_test(lambda u: u.user_type == 'ADMIN')
def stations_overview(request):
    stations = Station.objects.all().order_by('name')
    return render(request, 'time_tracking/admin/station/stations_overview.html', {
        'stations': stations
    })

@api_view(['PUT'])
@user_passes_test(lambda u: u.user_type == 'ADMIN')
def edit_station(request, station_id):
    try:
        station = Station.objects.get(id=station_id)
        data = json.loads(request.body)
        
        station.name = data.get('name', station.name)
        station.location = data.get('location', station.location)
        station.save()
        
        return JsonResponse({'status': 'success'})
    except Station.DoesNotExist:
        return JsonResponse({'error': 'Station not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@api_view(['DELETE'])
@user_passes_test(lambda u: u.user_type == 'ADMIN')
def delete_station(request, station_id):
    try:
        station = Station.objects.get(id=station_id)
        if station.customuser_set.exists():
            return JsonResponse({
                'error': 'Cannot delete station with assigned users'
            }, status=400)
        
        station.delete()
        return JsonResponse({'status': 'success'})
    except Station.DoesNotExist:
        return JsonResponse({'error': 'Station not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@api_view(['GET'])
@login_required
def get_worker_status(request, worker_id):
    try:
        worker = CustomUser.objects.get(
            id=worker_id,
            project_manager=request.user,
            user_type='TEMP_WORKER'
        )
        
        now = timezone.now()
        session_key = f"user_{worker.id}_last_active"
        last_active = request.session.get(session_key)
        
        # Check multiple activity indicators
        last_activity = worker.last_login
        recent_entry = TimeEntry.objects.filter(
            user=worker,
            timestamp__gte=now - timedelta(minutes=5)
        ).exists()
        
        # Get last action
        last_action = TimeEntry.objects.filter(
            user=worker,
            timestamp__date=now.date()
        ).order_by('-timestamp').first()

        # Consider user online if:
        # 1. They have a recent login
        # 2. They have made a recent entry
        # 3. They have recent session activity
        is_online = any([
            last_activity and (now - last_activity) < timedelta(minutes=5),
            recent_entry,
            last_active and (now - timezone.datetime.fromtimestamp(last_active, tz=timezone.utc)) < timedelta(minutes=5)
        ])
        
        response_data = {
            'is_online': is_online,
            'last_seen': last_activity.isoformat() if last_activity else None,
            'last_action': None
        }
        
        if last_action:
            response_data['last_action'] = {
                'type': last_action.entry_type,
                'timestamp': last_action.timestamp.isoformat(),
                'is_recent': (now - last_action.timestamp) < timedelta(minutes=5)
            }
        
        return JsonResponse(response_data)
        
    except CustomUser.DoesNotExist:
        return JsonResponse({'error': 'Worker not found'}, status=404)
    except Exception as e:
        logger.error(f"Error in get_worker_status: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
    
@api_view(['GET'])
@login_required
def get_worker_activity_log(request, worker_id):
    try:
        worker = CustomUser.objects.get(
            id=worker_id,
            project_manager=request.user,
            user_type='TEMP_WORKER'
        )
        
        # Get today's activities
        activities = TimeEntry.objects.filter(
            user=worker,
            timestamp__date=timezone.now().date()
        ).order_by('-timestamp')
        
        return JsonResponse({
            'activities': [{
                'type': entry.entry_type,
                'timestamp': entry.timestamp.isoformat(),
                'note': entry.note
            } for entry in activities]
        })
        
    except CustomUser.DoesNotExist:
        return JsonResponse({'error': 'Worker not found'}, status=404)