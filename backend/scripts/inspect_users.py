"""Simple script to dump users collection for debugging tokens/company mapping."""
from api.auth_utils import User
from pprint import pprint

users = User.find_all()
for u in users:
    pprint({
        'id': str(u.get('_id')),
        'username': u.get('username'),
        'company_id': u.get('company_id'),
        'token': u.get('token')[:8] + '...' if u.get('token') else None,
    })
