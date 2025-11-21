import hashlib, secrets
from datetime import datetime, timedelta
from api.mongo_models import Company
from .mongo_helper import MongoModel


class User(MongoModel):
    collection_name = 'users'

    @staticmethod
    def hash_password(password: str) -> str:
        salt = secrets.token_hex(8)
        h = hashlib.sha256((salt + password).encode()).hexdigest()
        return f'{salt}${h}'

    @staticmethod
    def verify_password(stored: str, password: str) -> bool:
        try:
            salt, h = stored.split('$', 1)
            return hashlib.sha256((salt + password).encode()).hexdigest() == h
        except Exception:
            return False

    @staticmethod
    def validate(data: dict) -> tuple[bool, str]:
        
        for f in ['username','password']:
            if f not in data or not data[f]:
                return False, f'Missing field {f}'
        # If role is provided, ensure it's valid
        role = data.get('role')
        if role is not None and role not in ('admin', 'manager'):
            return False, 'Invalid role. Must be "admin" or "manager".'
        return True, ''

    @staticmethod
    def generate_token() -> str:
        return secrets.token_hex(24)

    @classmethod
    def find_by_token(cls, token: str):
        return cls.find_one({'token': token})


def derive_company_id(request) -> str | None:
    """Extract company_id from user token if present."""
    token = request.headers.get('Authorization')
    if token and token.startswith('Token '):
        token = token[6:].strip()
    if not token:
        # Fallbacks: allow client to provide company_id as query param (company_id)
        # or as header `X-Auth-Company-Id`. This is intentionally permissive
        # for local development and debugging when Authorization header may be
        # missing due to proxy stripping.
        cid = request.headers.get('X-Auth-Company-Id') or request.GET.get('company_id')
        return cid
    user = User.find_one({'token': token})
    if user:
        return user.get('company_id')
    return None


def get_request_user(request):
    
    token = request.headers.get('Authorization')
    if token and token.startswith('Token '):
        token = token[6:].strip()
    if not token:
        return None
    return User.find_one({'token': token})
