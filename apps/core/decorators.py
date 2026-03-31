"""
Decorators reutilizáveis.
"""
from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect


def staff_required(view_func):
    """Decorator que requer usuário staff."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'Você não tem permissão para acessar esta página.')
            return redirect('dashboard-productivity')
        return view_func(request, *args, **kwargs)
    return wrapper


def ajax_required(view_func):
    """Decorator que requer requisição AJAX."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            messages.error(request, 'Esta ação requer uma requisição AJAX.')
            return redirect('dashboard-productivity')
        return view_func(request, *args, **kwargs)
    return wrapper
