
from __future__ import annotations

import threading
from typing import Optional, Dict

_local = threading.local()


def set_current_tenant(company_id: Optional[str]) -> None:
    _local.company_id = company_id


def get_current_tenant() -> Optional[str]:
    return getattr(_local, 'company_id', None)


def clear_current_tenant() -> None:
    if hasattr(_local, 'company_id'):
        del _local.company_id


def set_current_user(user: Optional[Dict]) -> None:
    _local.user = user


def get_current_user() -> Optional[Dict]:
    return getattr(_local, 'user', None)


def clear_current_user() -> None:
    if hasattr(_local, 'user'):
        del _local.user
