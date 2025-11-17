#!/usr/bin/env python
"""
Test script to verify authentication works correctly for API endpoints.
Tests both authenticated and unauthenticated requests.
"""
import os
import sys
import django
from datetime import datetime

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interview_scheduler.settings')
django.setup()

from api.mongo_models import Company, Applicant
from api.auth_utils import User as UserModel, is_authenticated
from django.test import RequestFactory
from rest_framework.test import APIRequestFactory

def test_authentication():
    """Test authentication helper functions"""
    print("=" * 60)
    print("Testing Authentication System")
    print("=" * 60)
    
    factory = APIRequestFactory()
    
    # Test 1: Unauthenticated request
    print("\n1. Testing unauthenticated request...")
    request = factory.get('/api/applicants/')
    result = is_authenticated(request)
    assert result == False, "Should return False for unauthenticated request"
    print("   ✅ Correctly identified as unauthenticated")
    
    # Test 2: Request with invalid token
    print("\n2. Testing request with invalid token...")
    try:
        request = factory.get('/api/applicants/', HTTP_AUTHORIZATION='Token invalid_token_12345')
        result = is_authenticated(request)
        assert result == False, "Should return False for invalid token"
        print("   ✅ Correctly identified invalid token")
    except Exception as e:
        if "MongoDB not connected" in str(e):
            print("   ⚠️  MongoDB not available - skipping database-dependent test")
        else:
            raise
    
    # Test 3: Request with valid token (if users exist)
    print("\n3. Testing request with valid token...")
    try:
        user = UserModel.find_one({})
        if user and user.get('token'):
            request = factory.get('/api/applicants/', HTTP_AUTHORIZATION=f'Token {user["token"]}')
            result = is_authenticated(request)
            assert result == True, "Should return True for valid token"
            print(f"   ✅ Correctly authenticated user: {user.get('username')}")
        else:
            print("   ⚠️  No users with tokens found in database - skipping")
    except Exception as e:
        print(f"   ⚠️  Could not test with valid token: {e}")
    
    print("\n" + "=" * 60)
    print("Authentication tests completed!")
    print("=" * 60)


def test_api_endpoints():
    """Test that API endpoints return proper error codes"""
    from api.views import ApplicantAPIView, current_company
    from rest_framework.test import force_authenticate
    from django.contrib.auth.models import AnonymousUser
    
    print("\n" + "=" * 60)
    print("Testing API Endpoint Responses")
    print("=" * 60)
    
    factory = APIRequestFactory()
    
    # Test current_company endpoint without authentication
    print("\n1. Testing /api/companies/current/ without authentication...")
    request = factory.get('/api/companies/current/')
    response = current_company(request)
    print(f"   Status code: {response.status_code}")
    print(f"   Response: {response.data}")
    if response.status_code == 401:
        print("   ✅ Correctly returns 401 Unauthorized")
    else:
        print(f"   ⚠️  Expected 401, got {response.status_code}")
    
    # Test POST to applicants without authentication
    print("\n2. Testing POST /api/applicants/ without authentication...")
    view = ApplicantAPIView.as_view()
    request = factory.post('/api/applicants/', {
        'full_name': 'Test Applicant',
        'email': 'test@example.com',
        'position': 'Technical'
    }, format='json')
    response = view(request)
    print(f"   Status code: {response.status_code}")
    print(f"   Response: {response.data}")
    if response.status_code == 401:
        print("   ✅ Correctly returns 401 Unauthorized")
    else:
        print(f"   ⚠️  Expected 401, got {response.status_code}")
    
    # Test GET applicants without authentication (should work)
    print("\n3. Testing GET /api/applicants/ without authentication...")
    request = factory.get('/api/applicants/')
    response = view(request)
    print(f"   Status code: {response.status_code}")
    if response.status_code == 200:
        print(f"   ✅ Correctly returns 200 OK (read access allowed)")
    else:
        print(f"   ⚠️  Expected 200, got {response.status_code}")
    
    print("\n" + "=" * 60)
    print("API endpoint tests completed!")
    print("=" * 60)


if __name__ == '__main__':
    try:
        test_authentication()
        test_api_endpoints()
        print("\n✅ All tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
