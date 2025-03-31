from django.shortcuts import render , redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import TempWorkerCreationForm
from .models import TimeEntry, CustomUser
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import ListView
from django.db.models import Sum, F
from datetime import timedelta

# Create your views here.
def is_admin(user):
    return user.user_type == 'ADMIN'

def is_project_manager(user):
    return user.user_type == 'PROJECT_MANAGER'

@user_passes_test(is_admin)
def create_temp_worker(request):
    if request.method == 'POST':
        form = TempWorkerCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin-dashboard')
    else:
        form = TempWorkerCreationForm()
    return render(request, 'time_tracking/create_temp_worker.html', {'form': form})

@login_required
def time_tracking_view(request):
    if request.user.user_type != 'TEMP_WORKER':
        return redirect('dashboard')
    return render(request, 'time_tracking/tracking.html')

class ProjectManagerDashbaord(UserPassesTestMixin, ListView):
    model = TimeEntry
    template_name = 'time_tracking/project_manager_dashboard.html'
    context_object_name = 'time_entries'
    paginate_by = 10
    ordering = ['-timestamp']

    def test_func(self):
        return is_project_manager(self.request.user)

    def get_queryset(self):
        return TimeEntry.objects.filter(
            user__project_manager=self.request.user
        ).select_related('user')

class AdminDashboard(UserPassesTestMixin, ListView):
    model = TimeEntry
    template_name = 'time_tracking/admin_dashboard.html'
    context_object_name = 'time_entries'

    def test_func(self):
        return self.request.user.user_type == 'ADMIN'
    
    def get_queryset(self):
        # Group entries by worker and date
        return TimeEntry.objects.select_related('user', 'user__station', 'user__project_manager').order_by('user','-timestamp')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        workers_data = {}

        for entry in self.get_queryset():
            worker = entry.user
            date = entry.timestamp.date()

            if worker not in workers_data:
                workers_data[worker][date] = {
                    'entries': [],
                    'total_work': timedelta(),
                    'total_break': timedelta(),
                    'notes': []
                }
            
            workers_data[worker][date]['entries'].append(entry)

            # Calculate work and break times
            if entry.entry_type == 'GEHEN' and workers_data[worker][date]['entries'][-2].entry_type == 'KOMMEN':
                work_time = entry.timestamp - workers_data[worker][date]['entries'][-2].timestamp
                workers_data[worker][date]['total_work'] += work_time
            
            if entry.entry_type == 'KOMMEN' and len(workers_data[worker][date]['entries']) > 1 and \
               workers_data[worker][date]['entries'][-2].entry_type == 'GEHEN':
                break_time = entry.timestamp - workers_data[worker][date]['entries'][-2].timestamp
                workers_data[worker][date]['total_break'] += break_time
            
            if entry.note:
                workers_data[worker][date]['notes'].append(entry.note)
        
        context['workers_data'] = workers_data
        return context
