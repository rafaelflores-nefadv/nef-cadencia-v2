"""
Service para gerenciamento de templates de mensagens.

Este service contém lógica de negócio para renderização e
gerenciamento de templates.
"""
from typing import Dict, Optional
from django.template import Template, Context
from django.core.exceptions import ValidationError
from ..models import MessageTemplate


def render_template(template: MessageTemplate, context_data: Dict) -> Dict[str, str]:
    """
    Renderiza um template de mensagem com contexto.
    
    Args:
        template: Template a renderizar
        context_data: Dados do contexto
    
    Returns:
        Dicionário com subject e body renderizados
    """
    context = Context(context_data)
    
    # Renderizar subject se existir
    rendered_subject = None
    if template.subject:
        subject_template = Template(template.subject)
        rendered_subject = subject_template.render(context)
    
    # Renderizar body
    body_template = Template(template.body)
    rendered_body = body_template.render(context)
    
    return {
        'subject': rendered_subject,
        'body': rendered_body,
    }


def get_active_template(template_type: str, channel: str) -> Optional[MessageTemplate]:
    """
    Busca template ativo por tipo e canal.
    
    Args:
        template_type: Tipo do template
        channel: Canal de comunicação
    
    Returns:
        MessageTemplate ou None
    """
    return MessageTemplate.objects.filter(
        template_type=template_type,
        channel=channel,
        active=True
    ).order_by('-version').first()


def validate_template_syntax(template_body: str) -> None:
    """
    Valida sintaxe do template Django.
    
    Args:
        template_body: Corpo do template
    
    Raises:
        ValidationError: Se sintaxe inválida
    """
    try:
        Template(template_body)
    except Exception as e:
        raise ValidationError(f'Sintaxe inválida no template: {str(e)}')


def create_template_version(
    base_template: MessageTemplate,
    new_body: str,
    new_subject: str = None,
    created_by=None
) -> MessageTemplate:
    """
    Cria nova versão de um template.
    
    Args:
        base_template: Template base
        new_body: Novo corpo
        new_subject: Novo subject (opcional)
        created_by: Usuário criador
    
    Returns:
        Novo template criado
    """
    # Validar sintaxe
    validate_template_syntax(new_body)
    if new_subject:
        validate_template_syntax(new_subject)
    
    # Desativar versão anterior
    base_template.active = False
    base_template.save()
    
    # Criar nova versão
    new_template = MessageTemplate.objects.create(
        name=base_template.name,
        template_type=base_template.template_type,
        channel=base_template.channel,
        subject=new_subject or base_template.subject,
        body=new_body,
        active=True,
        version=base_template.version + 1,
        updated_by=created_by,
    )
    
    return new_template


def get_template_variables(template_body: str) -> list:
    """
    Extrai variáveis usadas no template.
    
    Args:
        template_body: Corpo do template
    
    Returns:
        Lista de variáveis encontradas
    """
    import re
    
    # Encontrar variáveis no formato {{ variavel }}
    variables = re.findall(r'\{\{\s*(\w+)\s*\}\}', template_body)
    
    # Remover duplicatas e ordenar
    return sorted(set(variables))
