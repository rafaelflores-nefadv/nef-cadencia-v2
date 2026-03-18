"""
Formulários do app monitoring.
"""
from django import forms
from django.core.exceptions import ValidationError
from .models import Agent, PauseClassification, PauseCategoryChoices


class DashboardFilterForm(forms.Form):
    """Formulário de filtros do dashboard."""
    
    data_ref = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Data de Referência'
    )
    
    source = forms.ChoiceField(
        required=False,
        choices=[('', 'Todas as fontes')],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Fonte'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data


class AgentForm(forms.ModelForm):
    """Formulário de cadastro/edição de agente."""
    
    class Meta:
        model = Agent
        fields = [
            'cd_operador',
            'nm_agente',
            'nm_agente_code',
            'nr_ramal',
            'email',
            'ativo',
        ]
        widgets = {
            'cd_operador': forms.NumberInput(attrs={'min': 1, 'class': 'form-control'}),
            'nm_agente': forms.TextInput(attrs={'class': 'form-control'}),
            'nm_agente_code': forms.TextInput(attrs={'class': 'form-control'}),
            'nr_ramal': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_cd_operador(self):
        cd_operador = self.cleaned_data['cd_operador']
        
        if cd_operador <= 0:
            raise ValidationError('Código de operador deve ser positivo')
        
        # Verificar duplicação
        existing = Agent.objects.filter(cd_operador=cd_operador)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        
        if existing.exists():
            raise ValidationError('Código de operador já existe')
        
        return cd_operador
    
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        nr_ramal = cleaned_data.get('nr_ramal')
        
        # Validar que pelo menos email ou ramal está preenchido
        if not email and not nr_ramal:
            raise ValidationError('Informe pelo menos email ou ramal')
        
        return cleaned_data


class PauseClassificationForm(forms.ModelForm):
    """Formulário de classificação de pausas."""
    
    class Meta:
        model = PauseClassification
        fields = ['source', 'pause_name', 'category', 'is_active']
        widgets = {
            'source': forms.TextInput(attrs={'class': 'form-control'}),
            'pause_name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_pause_name(self):
        pause_name = self.cleaned_data['pause_name']
        if not pause_name or not pause_name.strip():
            raise ValidationError('Nome da pausa não pode ser vazio')
        return pause_name.strip()
