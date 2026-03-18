"""
Formulários do app assistant.
"""
from django import forms
from django.core.exceptions import ValidationError
from .models import AssistantUserPreference


class UserPreferenceForm(forms.ModelForm):
    """Formulário de preferências do usuário para o assistente."""
    
    class Meta:
        model = AssistantUserPreference
        fields = ['max_saved_conversations']
        widgets = {
            'max_saved_conversations': forms.NumberInput(
                attrs={'min': 1, 'max': 100, 'class': 'form-control'}
            ),
        }
    
    def clean_max_saved_conversations(self):
        value = self.cleaned_data['max_saved_conversations']
        
        if value < 1:
            raise ValidationError('O número mínimo de conversas é 1')
        
        if value > 100:
            raise ValidationError('O número máximo de conversas é 100')
        
        return value
