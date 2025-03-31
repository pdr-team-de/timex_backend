from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Station

class TempWorkerCreationForm(UserCreationForm):
    station = forms.ModelChoiceField(queryset=Station.objects.all())
    project_manager = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(user_type='PROJECT_MANAGER')
    )

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('first_name', 'last_name', 'station', 'project_manager', 'zeitarbeitsfirma')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'TEMP_WORKER'
        if commit:
            user.save()
        return user