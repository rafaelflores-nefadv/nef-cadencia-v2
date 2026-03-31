"""
Formulários do app messaging.
"""
from django import forms
from django.core.exceptions import ValidationError
from .models import MessageTemplate


class MessageTemplateForm(forms.ModelForm):
    """Formulário de criação/edição de template de mensagem."""
    
    class Meta:
        model = MessageTemplate
        fields = ['name', 'template_type', 'channel', 'subject', 'body', 'active', 'version']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'template_type': forms.Select(attrs={'class': 'form-control'}),
            'channel': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'body': forms.Textarea(attrs={'rows': 10, 'class': 'form-control'}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'version': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }
    
    def clean_name(self):
        name = self.cleaned_data['name']
        if not name or not name.strip():
            raise ValidationError('Nome do template não pode ser vazio')
        return name.strip()
    
    def clean_body(self):
        body = self.cleaned_data['body']
        if not body or not body.strip():
            raise ValidationError('Corpo do template não pode ser vazio')
        return body
