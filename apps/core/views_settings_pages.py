"""
Views para páginas filhas de Configurações.

Este módulo contém views específicas para cada seção de configurações,
permitindo navegação detalhada e gerenciamento granular.
"""
import json
import logging

from django.views.generic import TemplateView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

from apps.core.views import BasePageMixin
from apps.core.permissions_advanced import ConfigurationAccessMixin
from apps.core.selectors_settings import (
    get_system_configs_stats,
    get_integrations_stats,
    get_message_templates_stats,
    get_pause_classification_stats,
    get_assistant_stats,
    get_users_stats,
    get_operational_rules_stats,
    get_recent_config_changes,
)

logger = logging.getLogger("core")


class SettingsGeneralView(ConfigurationAccessMixin, BasePageMixin, TemplateView):
    """
    Página de configurações gerais do sistema.
    
    Exibe todas as configurações do sistema com opções de filtro e edição.
    """
    template_name = 'core/settings/general.html'
    
    page_title = 'Configurações Gerais'
    page_subtitle = 'Gerencie as configurações do sistema'
    
    def get_breadcrumbs(self):
        return [
            {'label': 'Dashboard', 'url': '/dashboard'},
            {'label': 'Configurações', 'url': reverse_lazy('settings-hub')},
            {'label': 'Gerais', 'url': None},
        ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estatísticas
        context['stats'] = get_system_configs_stats()
        
        # Alterações recentes
        context['recent_changes'] = get_recent_config_changes(limit=10)
        
        return context


class SettingsRulesView(ConfigurationAccessMixin, BasePageMixin, TemplateView):
    """
    Página de regras operacionais.
    
    Exibe e permite editar regras operacionais como thresholds e limites.
    """
    template_name = 'core/settings/rules.html'
    
    page_title = 'Regras Operacionais'
    page_subtitle = 'Configure thresholds, limites e alertas'
    
    def get_breadcrumbs(self):
        return [
            {'label': 'Dashboard', 'url': '/dashboard'},
            {'label': 'Configurações', 'url': reverse_lazy('settings-hub')},
            {'label': 'Regras', 'url': None},
        ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estatísticas
        context['stats'] = get_operational_rules_stats()
        
        return context


class SettingsIntegrationsView(ConfigurationAccessMixin, BasePageMixin, TemplateView):
    """
    Página de integrações.
    
    Exibe status e permite gerenciar integrações externas.
    """
    template_name = 'core/settings/integrations.html'
    
    page_title = 'Integrações'
    page_subtitle = 'Gerencie integrações com serviços externos'
    
    def get_breadcrumbs(self):
        return [
            {'label': 'Dashboard', 'url': '/dashboard'},
            {'label': 'Configurações', 'url': reverse_lazy('settings-hub')},
            {'label': 'Integrações', 'url': None},
        ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estatísticas
        context['stats'] = get_integrations_stats()
        
        return context


class SettingsTemplatesView(ConfigurationAccessMixin, BasePageMixin, TemplateView):
    """
    Página de templates de mensagens.
    
    Exibe e permite gerenciar templates de notificações.
    """
    template_name = 'core/settings/templates.html'
    
    page_title = 'Templates de Mensagens'
    page_subtitle = 'Gerencie templates de email, SMS e notificações'
    
    def get_breadcrumbs(self):
        return [
            {'label': 'Dashboard', 'url': '/dashboard'},
            {'label': 'Configurações', 'url': reverse_lazy('settings-hub')},
            {'label': 'Templates', 'url': None},
        ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estatísticas
        context['stats'] = get_message_templates_stats()
        
        return context


class SettingsAssistantView(ConfigurationAccessMixin, BasePageMixin, TemplateView):
    """
    Página de configurações do assistente IA.
    
    Exibe e permite configurar o assistente Eustácio.
    """
    template_name = 'core/settings/assistant.html'
    
    page_title = 'Assistente IA'
    page_subtitle = 'Configure o assistente Eustácio'
    
    def get_breadcrumbs(self):
        return [
            {'label': 'Dashboard', 'url': '/dashboard'},
            {'label': 'Configurações', 'url': reverse_lazy('settings-hub')},
            {'label': 'Assistente', 'url': None},
        ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estatísticas
        context['stats'] = get_assistant_stats()
        
        return context


class SettingsPauseClassificationView(ConfigurationAccessMixin, BasePageMixin, TemplateView):
    """
    Página de classificação de pausas.
    
    Exibe e permite gerenciar classificações de pausas operacionais.
    """
    template_name = 'core/settings/pause_classification.html'
    
    page_title = 'Classificação de Pausas'
    page_subtitle = 'Gerencie categorias e regras de pausas'
    
    def get_breadcrumbs(self):
        return [
            {'label': 'Dashboard', 'url': '/dashboard'},
            {'label': 'Configurações', 'url': reverse_lazy('settings-hub')},
            {'label': 'Pausas', 'url': None},
        ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estatísticas
        context['stats'] = get_pause_classification_stats()
        
        return context


class SettingsUsersView(ConfigurationAccessMixin, BasePageMixin, TemplateView):
    """
    Página de gestão de usuários.
    
    Exibe e permite gerenciar usuários e agentes do sistema.
    """
    template_name = 'core/settings/users.html'
    
    page_title = 'Gestão de Usuários'
    page_subtitle = 'Gerencie usuários, perfis e agentes'
    
    def get_breadcrumbs(self):
        return [
            {'label': 'Dashboard', 'url': '/dashboard'},
            {'label': 'Configurações', 'url': reverse_lazy('settings-hub')},
            {'label': 'Usuários', 'url': None},
        ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estatísticas
        context['stats'] = get_users_stats()
        
        return context


@login_required
@require_POST
def generate_operator_message_api(request):
    """
    API para gerar mensagens para operadores via OpenAI baseadas em regras de negócio.
    Recebe: { scenario, tone, operator_name, extra_context }
    Retorna: { message }
    """
    try:
        body = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON inválido."}, status=400)

    scenario = str(body.get("scenario") or "").strip()
    tone = str(body.get("tone") or "profissional").strip()
    operator_name = str(body.get("operator_name") or "operador").strip()
    extra_context = str(body.get("extra_context") or "").strip()

    if not scenario:
        return JsonResponse({"error": "Cenário obrigatório."}, status=400)

    SCENARIO_PROMPTS = {
        "baixa_ocupacao": "O operador está com taxa de ocupação abaixo do esperado (abaixo de 70%). Oriente-o a retomar atividades produtivas.",
        "pausa_excessiva": "O operador ultrapassou o tempo permitido em pausa. Solicite o retorno ao atendimento.",
        "pausa_improdutiva": "O operador está em pausa classificada como improdutiva (harmful). Informe sobre a política de pausas.",
        "sem_atividade": "O operador está logado porém sem nenhuma atividade registrada no sistema. Verifique se está ativo.",
        "boa_performance": "O operador está entre os melhores do ranking de produtividade. Reconheça e parabenize pelo desempenho.",
        "meta_atingida": "O operador atingiu a meta de ocupação do turno. Comunique o resultado positivo.",
        "alerta_critico": "Foi gerado um alerta crítico relacionado ao operador. Comunique de forma clara e peça ação imediata.",
        "inicio_turno": "O turno está começando. Envie uma mensagem motivacional e de boas-vindas ao operador.",
        "fim_turno": "O turno está encerrando. Agradeça a participação e informe sobre os resultados do dia.",
        "treinamento": "O operador precisa participar de um treinamento obrigatório. Comunique horário e instrução.",
    }

    TONE_INSTRUCTIONS = {
        "profissional": "Use tom profissional, direto e respeitoso.",
        "formal": "Use tom formal e corporativo, com linguagem séria.",
        "amigavel": "Use tom amigável, acolhedor e encorajador.",
        "urgente": "Use tom urgente e assertivo, deixando clara a necessidade de ação imediata.",
        "motivacional": "Use tom motivacional, positivo e energizante.",
    }

    scenario_instruction = SCENARIO_PROMPTS.get(scenario, scenario)
    tone_instruction = TONE_INSTRUCTIONS.get(tone, f"Use tom {tone}.")

    target_type = str(body.get("target_type") or "agente").strip()
    is_mass = target_type == "evento"

    if is_mass:
        prompt_parts = [
            "Você é um supervisor operacional de call center. Escreva uma mensagem curta e direta para um GRUPO de operadores (use o plural, fale com a equipe toda).",
            f"Contexto: {scenario_instruction}",
            f"Tom: {tone_instruction}",
            "A mensagem deve ter no máximo 3 frases. Use linguagem coletiva (ex: 'Equipe', 'Pessoal', 'Atenção a todos'). Vá direto ao ponto.",
            "Retorne APENAS o texto da mensagem, sem aspas, sem prefixos, sem explicações.",
        ]
    else:
        prompt_parts = [
            f"Você é um supervisor operacional de call center. Escreva uma mensagem curta e direta para o operador chamado {operator_name}.",
            f"Contexto: {scenario_instruction}",
            f"Tom: {tone_instruction}",
            "A mensagem deve ter no máximo 3 frases. Não use saudação longa. Vá direto ao ponto.",
            "Retorne APENAS o texto da mensagem, sem aspas, sem prefixos, sem explicações.",
        ]
    if extra_context:
        prompt_parts.insert(3, f"Informação adicional: {extra_context}")

    full_prompt = "\n".join(prompt_parts)

    try:
        from apps.assistant.services.openai_client import get_openai_client, OpenAIConfigError
        from apps.assistant.services.openai_settings import get_openai_settings

        client = get_openai_client()
        settings = get_openai_settings()
        model = settings.get("model", "gpt-4.1-mini")

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": full_prompt}],
            max_tokens=200,
            temperature=0.7,
        )
        message_text = (response.choices[0].message.content or "").strip()
        return JsonResponse({"message": message_text})

    except Exception as exc:
        logger.warning("generate_operator_message_api error: %s", exc)
        return JsonResponse({"error": f"Erro ao gerar mensagem: {exc}"}, status=502)
