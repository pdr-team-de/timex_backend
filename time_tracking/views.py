from django.shortcuts import render , redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import TimeEntry, CustomUser, Station, Zeitarbeitsfirma, Notification
from .forms import ProjectManagerCreationForm, TempWorkerCreationForm, TempFirmCreationForm
from django.contrib import messages
import logging
from django.urls import reverse

from django.http import JsonResponse
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .forms import generate_password
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib.auth.views import LoginView
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
logger = logging.getLogger(__name__)



# Create your views here.
def is_admin(user):
    return user.user_type == 'ADMIN'

def is_project_manager(user):
    return user.user_type == 'PROJECT_MANAGER'

@csrf_exempt
def generate_password_view(request):
    """Generate a new password and return it as JSON"""
    password = generate_password()
    print(f"Generated password: {password}")  # Debug output
    return JsonResponse({'password': password})

@user_passes_test(lambda u: u.user_type == 'ADMIN')
def create_temp_worker(request):
    if request.method == 'POST':
        form = TempWorkerCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # The form now handles everything
            messages.success(request, 
                f'Zeitarbeitskraft-Account wurde erfolgreich erstellt.\nZugangsdaten wurden per E-Mail an {user.email} gesendet.')
            return redirect('admin-dashboard')
    else:
        form = TempWorkerCreationForm()
        initial_password = generate_password()
    
    return render(request, 'time_tracking/admin/temp-worker/create_temp_worker.html', {
        'form': form,
        'initial_password': initial_password
    })

@user_passes_test(lambda u: u.user_type == 'ADMIN')
def create_project_manager(request):
    if request.method == 'POST':
        form = ProjectManagerCreationForm(request.POST)
        if form.is_valid():
            user, password = form.save()
            messages.success(request, 
                f'Project Manager account created successfully.\nUsername: {user.username}\nPassword: {password}')
            return redirect('admin-dashboard')
    else:
        form = ProjectManagerCreationForm()
    return render(request, 'time_tracking/admin/project-manager/create_project_manager.html', {'form': form})

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

@login_required
def time_tracking_view(request):
    if request.user.user_type != 'TEMP_WORKER':
        return redirect('admin-dashboard')
    return render(request, 'time_tracking/tracking.html')

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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([JSONParser])
def create_time_entry(request):
    try:
        # Validate user type
        if not request.user.is_authenticated:
            return Response({
                'status': 'error',
                'message': 'Nicht authentifiziert'
            }, status=401)

        if request.user.user_type != 'TEMP_WORKER':
            return Response({
                'status': 'error',
                'message': 'Nur Zeitarbeitskräfte können Zeiteinträge erstellen'
            }, status=403)

        # Validate entry type
        entry_type = request.data.get('type', '').upper()
        if entry_type not in dict(TimeEntry.ENTRY_TYPES).keys():
            return Response({
                'status': 'error',
                'message': 'Ungültiger Eintragstyp'
            }, status=400)

        # Create entry
        entry = TimeEntry.objects.create(
            user=request.user,
            entry_type=entry_type,
            note=request.data.get('note'),
            timestamp=timezone.now()
        )

        # Notify project manager for FEIERABEND
        if entry_type == 'FEIERABEND' and request.user.project_manager:
            Notification.objects.create(
                user=request.user.project_manager,
                type='FEIERABEND',
                title='Arbeitstag beendet',
                message=f'{request.user.get_full_name()} hat den Arbeitstag beendet',
                entry=entry
            )

        return Response({
            'status': 'success',
            'data': {
                'id': entry.id,
                'timestamp': entry.timestamp.isoformat(),
                'type': entry.entry_type,
                'note': entry.note
            }
        }, status=201)

    except Exception as e:
        return Response({
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

def imprint(request):
    return render(request, 'time_tracking/legal/imprint.html')

def privacy_policy(request):
    return render(request, 'time_tracking/legal/privacy_policy.html')