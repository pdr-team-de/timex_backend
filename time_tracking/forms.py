from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.mail import send_mail
from django.conf import settings
from .models import CustomUser, Station, Zeitarbeitsfirma, generate_unique_username
import random
import string
import ssl
import certifi

class BaseUserCreationForm(forms.ModelForm):
    email = forms.EmailField(required=True)

    def send_credentials_email(self, user, password):
        try:
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
                fail_silently=False
            )
        except Exception as e:
            print(f"Email sending failed: {str(e)}")
            # You might want to add proper error handling here
            # For now, we'll still create the user but log the email failure
            pass

class TempWorkerCreationForm(BaseUserCreationForm):
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
    generated_password = forms.CharField(widget=forms.HiddenInput(), required=False)

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
        
        # Generate unique username
        base_username = f"{self.cleaned_data['first_name'].lower()}.{self.cleaned_data['last_name'].lower()}"
        user.username = generate_unique_username(base_username, CustomUser)
        
        password = self.cleaned_data.get('generated_password') or generate_password()
        user.set_password(password)
        
        if commit:
            user.save()
            self.send_credentials_email(user, password)
    
        return user

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
        
        # Generate unique username
        base_username = f"{self.cleaned_data['first_name'].lower()}.{self.cleaned_data['last_name'].lower()}"
        user.username = generate_unique_username(base_username, CustomUser)
        
        password = generate_password()
        user.set_password(password)
        
        if commit:
            user.save()
            self.send_credentials_email(user, password)
            
        return user, password

class TempFirmCreationForm(forms.ModelForm):
    class Meta:
        model = Zeitarbeitsfirma
        fields = ('name', 'address', 'contact_person')
        labels = {
            'name': 'Name',
            'address': 'Adresse',
            'contact_person': 'Ansprechpartner'
        }

    def save(self, commit=True):
        temp_firm = super().save(commit=False)
        temp_firm.name = self.cleaned_data['name']
        temp_firm.address = self.cleaned_data['address']
        temp_firm.contact_person = self.cleaned_data['contact_person']
        if commit:
            temp_firm.save()
        return temp_firm

def generate_password():
    lowercase = ''.join(random.choices(string.ascii_lowercase, k=2))
    uppercase = ''.join(random.choices(string.ascii_uppercase, k=3))
    digits = ''.join(random.choices(string.digits, k=2))
    special = random.choice('!@#$%^&*')
    
    # Combine all characters and shuffle
    password_list = list(lowercase + uppercase + digits + special)
    random.shuffle(password_list)
    return ''.join(password_list)