# Authentication System Documentation

## Overview

The Interview Scheduler API uses a custom token-based authentication system. This document explains how authentication works and which endpoints require authentication.

## How Authentication Works

### Token-Based Authentication

1. **User Registration**: Users register via `/api/auth/register/` with username, password, and company information
2. **User Login**: Users login via `/api/auth/login/` with username and password
3. **Token Generation**: Upon successful login, the API returns an authentication token
4. **Token Storage**: The frontend stores this token in localStorage as `auth_token`
5. **Token Usage**: For authenticated requests, the token is sent in the Authorization header:
   ```
   Authorization: Token <your_token_here>
   ```

### Authentication Helper Functions

Located in `api/auth_utils.py`:

- **`derive_company_id(request)`**: Extracts the company_id from the authenticated user's token. Returns `None` if not authenticated.
- **`is_authenticated(request)`**: Returns `True` if the request has a valid authentication token, `False` otherwise.
- **`get_request_user(request)`**: Returns the user document for the authenticated user, or `None` if not authenticated.

## API Endpoints Authentication Requirements

### Public Endpoints (No Authentication Required)

These endpoints can be accessed without authentication:

- **POST** `/api/auth/register/` - Register a new user
- **POST** `/api/auth/login/` - Login and get authentication token
- **GET** `/api/applicants/` - List applicants (read-only)
- **GET** `/api/applicants/{id}/` - Get specific applicant (read-only)
- **GET** `/api/interviewers/` - List interviewers (read-only)
- **GET** `/api/interviewers/{id}/` - Get specific interviewer (read-only)
- **GET** `/api/rooms/` - List rooms (read-only)
- **GET** `/api/rooms/{id}/` - Get specific room (read-only)
- **GET** `/api/schedules/` - List schedules (read-only)
- **GET** `/api/schedules/{id}/` - Get specific schedule (read-only)
- **GET** `/api/schedules/timeline/` - Get schedule timeline (read-only)
- **GET** `/api/positions/` - List positions (read-only)
- **GET** `/api/sessions/` - List interview sessions (read-only)

### Protected Endpoints (Authentication Required)

These endpoints require a valid authentication token:

#### Company Management
- **GET** `/api/companies/current/` - Get current user's company
- **GET** `/api/companies/` - List companies
- **GET** `/api/companies/{id}/` - Get specific company
- **PUT** `/api/companies/{id}/` - Update company

#### Data Management (Write Operations)
- **POST** `/api/applicants/` - Create applicant
- **PUT** `/api/applicants/{id}/` - Update applicant
- **DELETE** `/api/applicants/{id}/` - Delete applicant
- **POST** `/api/interviewers/` - Create interviewer
- **PUT** `/api/interviewers/{id}/` - Update interviewer
- **DELETE** `/api/interviewers/{id}/` - Delete interviewer
- **POST** `/api/rooms/` - Create room
- **PUT** `/api/rooms/{id}/` - Update room
- **DELETE** `/api/rooms/{id}/` - Delete room
- **POST** `/api/schedules/` - Create schedule
- **PUT** `/api/schedules/{id}/` - Update schedule
- **DELETE** `/api/schedules/{id}/` - Delete schedule

#### Algorithm Operations
- **POST** `/api/algorithm/genetic/` - Run genetic algorithm
- **POST** `/api/algorithm/genetic-variant/` - Run GA variant
- **POST** `/api/algorithm/genetic-variant2/` - Run GA variant 2
- **POST** `/api/algorithm/genetic-variant3/` - Run GA variant 3
- **POST** `/api/algorithm/compare/` - Compare algorithms
- **POST** `/api/algorithm/topk/` - Generate top-k schedules
- **POST** `/api/algorithm/select/` - Choose schedule result
- **GET** `/api/algorithm/results/` - Get algorithm results (may require auth based on filtering)

#### Data Import/Export
- **POST** `/api/data/import/` - Import Excel data
- **GET** `/api/data/export/` - Export schedules
- **GET** `/api/data/statistics/` - Get dashboard statistics
- **GET** `/api/data/logs/` - Get action logs (admin/manager only)

#### Session Management
- **POST** `/api/sessions/` - Create interview session
- **PUT** `/api/sessions/{id}/` - Update interview session
- **DELETE** `/api/sessions/{id}/` - Delete interview session
- **POST** `/api/sessions/{id}/activate/` - Activate session
- **POST** `/api/sessions/{id}/membership/` - Update session membership

## Error Responses

### 401 Unauthorized

When authentication is required but not provided or invalid:

```json
{
  "error": "Authentication required",
  "detail": "Please login to access this resource",
  "auth_required": true
}
```

### 404 Not Found

When a resource is not found or company doesn't exist:

```json
{
  "error": "No companies available",
  "detail": "Please contact administrator to set up a company"
}
```

## Frontend Integration

### Storing the Token

After successful login:

```javascript
const response = await authAPI.login({ username, password });
localStorage.setItem("auth_token", response.data.token);
localStorage.setItem("auth_company_id", response.data.company_id);
```

### Sending Authenticated Requests

The axios interceptor automatically adds the token to requests:

```javascript
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("auth_token");
  if (token) {
    config.headers = config.headers || {};
    config.headers["Authorization"] = `Token ${token}`;
  }
  return config;
});
```

### Handling 401 Errors

When a 401 error is received, the frontend should:

1. Clear the stored token
2. Redirect to the login page
3. Show an appropriate message to the user

Example:

```javascript
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear token and redirect to login
      localStorage.removeItem("auth_token");
      localStorage.removeItem("auth_company_id");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);
```

## Security Considerations

1. **Token Storage**: Tokens are stored in the User collection in MongoDB with SHA-256 hashing
2. **Token Generation**: Tokens are generated using Python's `secrets.token_hex(24)` for cryptographic security
3. **Company Scoping**: Most operations are automatically scoped to the authenticated user's company
4. **Role-Based Access**: The system supports `admin` and `manager` roles for different permission levels
5. **Read-Only Public Access**: GET endpoints are public to allow viewing data, but write operations require authentication

## Implementation Details

### Adding Authentication to a New Endpoint

To add authentication to a new endpoint:

```python
from api.auth_utils import is_authenticated, derive_company_id

@api_view(['POST'])
def my_protected_endpoint(request):
    # Check authentication
    if not is_authenticated(request):
        return Response({
            'error': 'Authentication required',
            'detail': 'Please login to access this resource'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    # Get user's company
    company_id = derive_company_id(request)
    
    # Your endpoint logic here
    ...
```

For class-based views:

```python
class MyAPIView(APIView):
    def post(self, request):
        if not is_authenticated(request):
            return Response({
                'error': 'Authentication required',
                'detail': 'Please login to create resources'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Your logic here
        ...
```

## Testing Authentication

See `backend/scripts/test_authentication.py` for example tests.

To test manually:

1. **Without authentication**:
   ```bash
   curl -X GET http://localhost:8000/api/companies/current/
   # Expected: 401 Unauthorized
   ```

2. **With authentication**:
   ```bash
   # First login
   TOKEN=$(curl -X POST http://localhost:8000/api/auth/login/ \
     -H "Content-Type: application/json" \
     -d '{"username":"demo","password":"demo123"}' \
     | jq -r '.token')
   
   # Then use the token
   curl -X GET http://localhost:8000/api/companies/current/ \
     -H "Authorization: Token $TOKEN"
   # Expected: 200 OK with company data
   ```

## Troubleshooting

### Issue: "Authentication required" on all endpoints

**Solution**: Ensure you've logged in and the token is being sent:
1. Check that `localStorage.getItem("auth_token")` returns a value
2. Verify the Authorization header is present in network requests
3. Check that the token format is `Token <token_value>`, not just `<token_value>`

### Issue: 401 error after successful login

**Solution**: The token might have been invalidated:
1. Login again to get a fresh token
2. Check that the user document in MongoDB has a valid token field
3. Verify the token hasn't been rotated (tokens are rotated on each login)

### Issue: Can't access company data

**Solution**: Ensure the user is associated with a company:
1. Check that the user document has a `company_id` field
2. Verify the company exists in the database
3. The `/api/companies/current/` endpoint will auto-assign the first available company if none is set
