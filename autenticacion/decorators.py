# autenticacion/decorators.py
from django.http import HttpResponseForbidden
from functools import wraps

def rol_requerido(roles_permitidos):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.rol not in roles_permitidos and request.user.rol != 'admin':
                return HttpResponseForbidden("No tienes permisos para acceder a esta sección")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator