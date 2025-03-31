from django.contrib import admin
from .models import CustomUser, Station, Zeitarbeitsfirma, TimeEntry

# Register your models here.


@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ('user', 'entry_type', 'timestamp', 'note')
    list_filter = ('user', 'entry_type', 'timestamp')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'note')
    date_hierarchy = 'timestamp'

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name', 'user_type', 'station')
    list_filter = ('user_type', 'station')
    search_fields = ('username', 'first_name', 'last_name')

@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ('name', 'location')
    search_fields = ('name', 'location')

@admin.register(Zeitarbeitsfirma)
class ZeitarbeitsfirmaAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'contact_person')
    search_fields = ('name', 'address', 'contact_person')