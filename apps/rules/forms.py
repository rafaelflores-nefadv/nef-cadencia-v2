"""
Formulários do app rules.
"""
from django import forms
from django.core.exceptions import ValidationError
from .models import SystemConfig, SystemConfigValueType
import json


class SystemConfigForm(forms.ModelForm):
    """Formulário de edição de configuração do sistema."""
    
    class Meta:
        model = SystemConfig
        fields = ['config_value', 'description']
        widgets = {
            'config_value': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.value_type:
            # Ajustar widget baseado no tipo
            if self.instance.value_type == SystemConfigValueType.BOOL:
                self.fields['config_value'].widget = forms.Select(
                    choices=[('true', 'Sim'), ('false', 'Não')],
                    attrs={'class': 'form-control'}
                )
            elif self.instance.value_type == SystemConfigValueType.INT:
                self.fields['config_value'].widget = forms.NumberInput(
                    attrs={'class': 'form-control'}
                )
    
    def clean_config_value(self):
        value = self.cleaned_data['config_value']
        value_type = self.instance.value_type
        
        # Validar baseado no tipo
        if value_type == SystemConfigValueType.INT:
            try:
                int(value)
            except ValueError:
                raise ValidationError('Valor deve ser um número inteiro')
        
        elif value_type == SystemConfigValueType.BOOL:
            if value.lower() not in ['true', 'false', '1', '0']:
                raise ValidationError('Valor deve ser true ou false')
        
        elif value_type == SystemConfigValueType.JSON:
            try:
                json.loads(value)
            except json.JSONDecodeError:
                raise ValidationError('Valor deve ser um JSON válido')
        
        return value
