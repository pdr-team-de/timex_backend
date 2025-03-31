from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
class Station(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)

    def __str__(self):
        return self.name
    

class Zeitarbeitsfirma(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255)

    def __str__(self):
        return self.name
    
#Custom User is  a class which extends AbstractUser
class CustomUser(AbstractUser):
    USER_TYPES = (
        ('ADMIN', 'Administrator'),
        ('PROJECT_MANAGER', 'Projektleiter'),
        ('TEMP_WORKER', 'Zeitarbeitskraft'),
    )

    user_type = models.CharField(max_length=20, choices=USER_TYPES)
    station = models.ForeignKey(Station, on_delete=models.SET_NULL, null=True, blank=True)
    zeitarbeitsfirma = models.ForeignKey(Zeitarbeitsfirma, on_delete=models.SET_NULL, null=True, blank=True)
    project_manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                        limit_choices_to={'user_type': 'PROJECT_MANAGER'})
    
    def save(self, *args, **kwargs):
        if not self.username and self.first_name and self.last_name:
            self.username = f"{self.first_name.lower()}.{self.last_name.lower()}"
        super().save(*args, **kwargs)

class TimeEntry(models.Model):
    ENTRY_TYPES = (
        ('KOMMEN', 'Kommen'),
        ('GEHEN', 'Gehen'),
        ('FEIERABEND', 'Feierabend'),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    entry_type = models.CharField(max_length=20, choices=ENTRY_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    note = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']