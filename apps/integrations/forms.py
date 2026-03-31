"""
Formulários do app integrations.
"""
from django import forms
from django.core.exceptions import ValidationError
from .models import Integration
import json


class IntegrationForm(forms.ModelForm):
    """Formulário de criação/edição de integração."""
    
    class Meta:
        model = Integration
        fields = ['name', 'channel', 'enabled', 'config_json']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'channel': forms.Select(attrs={'class': 'form-control'}),
            'enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'config_json': forms.Textarea(attrs={'rows': 10, 'class': 'form-control'}),
        }
    
    def clean_name(self):
        name = self.cleaned_data['name']
        if not name or not name.strip():
            raise ValidationError('Nome da integração não pode ser vazio')
        return name.strip()
    
    def clean_config_json(self):
        config = self.cleaned_data['config_json']
        
        # Se for string, tentar parsear como JSON
        if isinstance(config, str):
            try:
                json.loads(config)
            except json.JSONDecodeError:
                raise ValidationError('Configuração deve ser um JSON válido')
        
        return config
