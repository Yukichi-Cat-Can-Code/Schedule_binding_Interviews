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
        """Validate user data.

        Required fields:
          - username
          - password

        Optional but recommended for RBAC:
          - role: "admin" or "manager" (defaults handled at creation time)
          - company_id: for manager-scoped accounts
        """
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
    """Extract company_id from user token if present.
    
    Returns None if user is not authenticated.
    """
    token = request.headers.get('Authorization')
    if token and token.startswith('Token '):
        token = token[6:].strip()
    if not token:
        return None
    user = User.find_one({'token': token})
    if user:
        return user.get('company_id')
    return None


def is_authenticated(request) -> bool:
    """Check if the request has a valid authentication token.
    
    Returns True if user is authenticated, False otherwise.
    """
    token = request.headers.get('Authorization')
    if token and token.startswith('Token '):
        token = token[6:].strip()
    if not token:
        return False
    user = User.find_one({'token': token})
    return user is not None


def get_request_user(request):
    """Resolve current user from Authorization header token.

    Returns a dict-like user document or None. This is a helper for
    lightweight RBAC checks without changing existing call sites.
    """
    token = request.headers.get('Authorization')
    if token and token.startswith('Token '):
        token = token[6:].strip()
    if not token:
        return None
    return User.find_one({'token': token})
