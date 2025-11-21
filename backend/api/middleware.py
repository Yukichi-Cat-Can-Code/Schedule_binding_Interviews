"""Django middleware to set tenant and user context for each request.

This middleware reads the Authorization header (Token ...) and uses
`auth_utils.derive_company_id` and `auth_utils.get_request_user` to set
thread-local context via `api.tenant` helpers so lower-layer code can
enforce tenant scoping automatically.
"""
from __future__ import annotations

from typing import Callable
from django.utils.deprecation import MiddlewareMixin
from .auth_utils import derive_company_id, get_request_user
from .tenant import set_current_tenant, clear_current_tenant, set_current_user, clear_current_user


class TenantMiddleware(MiddlewareMixin):
    def process_request(self, request):
        try:
            cid = derive_company_id(request)
            set_current_tenant(cid)
            user = get_request_user(request)
            set_current_user(user)
        except Exception:
            # be defensive: clear context on failure
            clear_current_tenant()
            clear_current_user()

    def process_response(self, request, response):
        clear_current_tenant()
        clear_current_user()
        return response
