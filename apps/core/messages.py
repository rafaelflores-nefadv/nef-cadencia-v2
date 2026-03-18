"""
Sistema centralizado de mensagens padronizadas.
"""
from django.contrib import messages as django_messages


class Messages:
    """
    Classe para mensagens padronizadas do sistema.
    """
    
    # Mensagens de sucesso
    CREATED_SUCCESS = "{item} criado com sucesso."
    UPDATED_SUCCESS = "{item} atualizado com sucesso."
    DELETED_SUCCESS = "{item} removido com sucesso."
    SAVED_SUCCESS = "Dados salvos com sucesso."
    
    # Mensagens de erro
    CREATED_ERROR = "Erro ao criar {item}."
    UPDATED_ERROR = "Erro ao atualizar {item}."
    DELETED_ERROR = "Erro ao remover {item}."
    SAVED_ERROR = "Erro ao salvar dados."
    PERMISSION_DENIED = "Você não tem permissão para realizar esta ação."
    NOT_FOUND = "{item} não encontrado."
    INVALID_DATA = "Dados inválidos. Verifique os campos e tente novamente."
    
    # Mensagens de aviso
    CONFIRM_DELETE = "Tem certeza que deseja remover {item}?"
    UNSAVED_CHANGES = "Você tem alterações não salvas."
    
    # Mensagens de informação
    NO_RESULTS = "Nenhum resultado encontrado."
    LOADING = "Carregando..."
    PROCESSING = "Processando..."
    
    @staticmethod
    def success(request, message, **kwargs):
        """Adiciona mensagem de sucesso."""
        django_messages.success(request, message.format(**kwargs))
    
    @staticmethod
    def error(request, message, **kwargs):
        """Adiciona mensagem de erro."""
        django_messages.error(request, message.format(**kwargs))
    
    @staticmethod
    def warning(request, message, **kwargs):
        """Adiciona mensagem de aviso."""
        django_messages.warning(request, message.format(**kwargs))
    
    @staticmethod
    def info(request, message, **kwargs):
        """Adiciona mensagem de informação."""
        django_messages.info(request, message.format(**kwargs))
    
    @staticmethod
    def created(request, item_name):
        """Mensagem padrão de criação."""
        django_messages.success(request, Messages.CREATED_SUCCESS.format(item=item_name))
    
    @staticmethod
    def updated(request, item_name):
        """Mensagem padrão de atualização."""
        django_messages.success(request, Messages.UPDATED_SUCCESS.format(item=item_name))
    
    @staticmethod
    def deleted(request, item_name):
        """Mensagem padrão de deleção."""
        django_messages.success(request, Messages.DELETED_SUCCESS.format(item=item_name))
