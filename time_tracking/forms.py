from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.mail import send_mail
from django.conf import settings
from .models import CustomUser, Station, Zeitarbeitsfirma
import random
import string

class BaseUserCreationForm(forms.ModelForm):
    email = forms.EmailField(required=True)

    def send_credentials_email(self, user, password):
        subject = 'Ihre Zugangsdaten - TimeX by PDR-Team'
        message = f"""
        Sehr geehrte(r) {user.first_name} {user.last_name},

        Ihre Zugangsdaten für das PDR Zeiterfassungssystem lauten:
        
        Benutzername: {user.username}
        Passwort: {password}
        
        Bitte ändern Sie Ihr Passwort bei der ersten Anmeldung.
        
        Mit freundlichen Grüßen
        Ihr PDR-Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

class TempWorkerCreationForm(UserCreationForm):
    station = forms.ModelChoiceField(
        queryset=Station.objects.all(),
        label='Station'
    )
    project_manager = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(user_type='PROJECT_MANAGER'),
        label='Projektleiter'
    )
    zeitarbeitsfirma = forms.ModelChoiceField(
        queryset=Zeitarbeitsfirma.objects.all(),
        required=True,
        label='Zeitarbeitsfirma'
    )

    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'station', 'project_manager', 'zeitarbeitsfirma')
        labels = {
            'first_name': 'Vorname',
            'last_name': 'Nachname',
            'email': 'E-Mail'
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'TEMP_WORKER'
        user.username = f"{self.cleaned_data['first_name'].lower()}.{self.cleaned_data['last_name'].lower()}"
        password = generate_password()
        user.set_password(password)
        
        if commit:
            user.save()
            self.send_credentials_email(user, password)
            
        return user, password

class ProjectManagerCreationForm(BaseUserCreationForm):
    station = forms.ModelChoiceField(
        queryset=Station.objects.all(),
        label='Station'
    )

    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'station')
        labels = {
            'first_name': 'Vorname',
            'last_name': 'Nachname',
            'email': 'E-Mail'
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'PROJECT_MANAGER'
        user.username = f"{self.cleaned_data['first_name'].lower()}.{self.cleaned_data['last_name'].lower()}"
        password = generate_password()
        user.set_password(password)
        
        if commit:
            user.save()
            self.send_credentials_email(user, password)
            
        return user, password


def generate_password():
    lowercase = ''.join(random.choices(string.ascii_lowercase, k=2))
    uppercase = ''.join(random.choices(string.ascii_uppercase, k=3))
    digits = ''.join(random.choices(string.digits, k=2))
    special = random.choice('!@#$%^&*')
    
    # Combine all characters and shuffle
    password_list = list(lowercase + uppercase + digits + special)
    random.shuffle(password_list)
    return ''.join(password_list)