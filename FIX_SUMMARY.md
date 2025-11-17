# Fix for API Unauthorized Access Errors

## Problem Summary

The Interview Scheduler application was experiencing HTTP 401 (Unauthorized) and 404 (Not Found) errors when users tried to access various API endpoints. The root causes were:

1. The `current_company` endpoint didn't properly check for authentication before attempting operations
2. Write operations (POST/PUT/DELETE) didn't consistently require authentication
3. Error messages were unclear about why requests were failing
4. When `derive_company_id` returned None (no authentication), subsequent operations would fail unexpectedly

## Solution Overview

This fix implements consistent authentication checking across the API with clear, actionable error messages.

### Key Changes

1. **Added `is_authenticated()` helper function** (`api/auth_utils.py`)
   - Checks if a request has a valid authentication token
   - Returns boolean for easy use in views
   - Handles edge cases gracefully

2. **Updated `current_company` endpoint** (`api/views.py`)
   - Now requires authentication
   - Returns 401 with clear error message if not authenticated
   - Provides helpful guidance to users about logging in

3. **Added authentication to write operations**
   - All POST/PUT/DELETE methods now check authentication
   - Applied to: ApplicantAPIView, InterviewerAPIView, RoomAPIView, ScheduleAPIView
   - Returns consistent 401 errors with actionable messages

4. **Maintained public read access**
   - GET endpoints remain accessible without authentication
   - Allows users to browse data before logging in
   - Aligns with demo/educational nature of the project

## Error Message Improvements

### Before
```json
{
  "detail": "No companies available"
}
```

### After
```json
{
  "error": "Authentication required",
  "detail": "Please login to access company information",
  "auth_required": true
}
```

## Files Modified

- `backend/api/auth_utils.py` - Added `is_authenticated()` function
- `backend/api/views.py` - Updated authentication checks in multiple views
- `AUTHENTICATION.md` - Comprehensive documentation of authentication system
- `backend/scripts/test_authentication.py` - Test script for validation

## Testing the Fix

### Prerequisites

1. Ensure MongoDB is running and configured
2. Run the sample data import script to create test users

### Test Scenarios

#### Scenario 1: Unauthenticated access to protected endpoint

**Request:**
```bash
curl -X GET http://localhost:8000/api/companies/current/
```

**Expected Response:**
```json
{
  "error": "Authentication required",
  "detail": "Please login to access company information",
  "auth_required": true
}
```

**Status Code:** 401 Unauthorized

#### Scenario 2: Authenticated access to protected endpoint

**Request:**
```bash
# First login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"demo123"}'

# Response includes token
# {"id":"...","username":"demo","company_id":"...","token":"abc123..."}

# Use token to access protected endpoint
curl -X GET http://localhost:8000/api/companies/current/ \
  -H "Authorization: Token abc123..."
```

**Expected Response:**
```json
{
  "id": "...",
  "name": "Demo Company",
  "code": "DEMO",
  "created_at": "..."
}
```

**Status Code:** 200 OK

#### Scenario 3: Unauthenticated write operation

**Request:**
```bash
curl -X POST http://localhost:8000/api/applicants/ \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Test User",
    "email": "test@example.com",
    "position": "Technical"
  }'
```

**Expected Response:**
```json
{
  "error": "Authentication required",
  "detail": "Please login to create applicants"
}
```

**Status Code:** 401 Unauthorized

#### Scenario 4: Read-only access without authentication (allowed)

**Request:**
```bash
curl -X GET http://localhost:8000/api/applicants/
```

**Expected Response:**
```json
[
  {
    "id": "...",
    "full_name": "...",
    "email": "...",
    ...
  }
]
```

**Status Code:** 200 OK

## Frontend Integration

### Handling 401 Errors

The frontend should be updated to handle 401 errors by redirecting users to login:

```javascript
// In api.js or similar
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear stored authentication
      localStorage.removeItem("auth_token");
      localStorage.removeItem("auth_company_id");
      
      // Redirect to login page
      window.location.href = "/login";
      
      // Show user-friendly message
      toast.error("Please login to continue");
    }
    return Promise.reject(error);
  }
);
```

### Login Flow

1. User submits login form
2. Frontend calls `/api/auth/login/`
3. On success, store token in localStorage
4. Subsequent requests include token in Authorization header
5. If 401 is received, redirect to login

## Migration Notes

### For Existing Users

If you have existing code that relies on unauthenticated access to write endpoints, you'll need to:

1. Ensure users are logged in before attempting write operations
2. Handle 401 errors gracefully in your frontend
3. Update any scripts or automated tools to include authentication tokens

### For New Users

1. Start by logging in via `/api/auth/login/`
2. Store the returned token
3. Include the token in all subsequent requests that modify data
4. Read operations work without authentication

## Security Considerations

### What's Protected

- All write operations (POST/PUT/DELETE) require authentication
- Company information requires authentication
- Algorithm execution requires authentication
- Data import/export requires authentication

### What's Public

- Read-only access to applicants, interviewers, rooms, schedules
- User registration (`/api/auth/register/`)
- User login (`/api/auth/login/`)

### Why This Approach

1. **Educational Demo**: The project is for learning, so read-only public access helps users explore
2. **Data Protection**: Write operations are protected to prevent unauthorized modifications
3. **User Experience**: Clear error messages help users understand what they need to do
4. **Scalability**: The design supports future enhancements like role-based permissions

## Troubleshooting

### Issue: All requests return 401

**Check:**
- Is the token being sent in requests?
- Is the token format correct? Should be `Token <token_value>`
- Has the token expired or been rotated?

**Solution:**
- Re-login to get a fresh token
- Verify the Authorization header in network inspector

### Issue: Can't create any data after logging in

**Check:**
- Is the company_id set for the user?
- Does the company exist in the database?

**Solution:**
- Access `/api/companies/current/` to trigger auto-assignment
- Run the sample data import script

### Issue: 404 errors instead of 401

**Check:**
- Is the endpoint URL correct?
- Is the Django server running?

**Solution:**
- Verify the API route exists in `api/urls.py`
- Check Django server logs for routing errors

## Next Steps

### Recommended Enhancements

1. **Add Token Expiration**: Currently tokens don't expire; consider adding TTL
2. **Implement Refresh Tokens**: Allow users to refresh expired tokens without re-login
3. **Add Rate Limiting**: Protect against brute force attacks on login
4. **Enhanced RBAC**: Expand role-based access control beyond admin/manager
5. **Audit Logging**: Log all authentication events for security monitoring

### Testing Checklist

- [ ] Login with valid credentials
- [ ] Login with invalid credentials
- [ ] Access protected endpoint without token
- [ ] Access protected endpoint with valid token
- [ ] Access protected endpoint with invalid token
- [ ] Try write operation without authentication
- [ ] Try write operation with authentication
- [ ] Verify read-only endpoints work without auth
- [ ] Verify error messages are clear and helpful

## Documentation

For detailed information about the authentication system, see [AUTHENTICATION.md](./AUTHENTICATION.md).

## Support

If you encounter issues with authentication:

1. Check the AUTHENTICATION.md documentation
2. Review Django server logs for detailed error messages
3. Verify your MongoDB connection is working
4. Ensure sample data has been imported (includes test users)
5. Test with the provided test script: `python backend/scripts/test_authentication.py`

## Summary

This fix resolves the HTTP 401 and 404 errors by:
- ✅ Adding consistent authentication checks
- ✅ Providing clear, actionable error messages
- ✅ Maintaining backward compatibility for read operations
- ✅ Documenting the authentication system
- ✅ Adding validation tests

The changes ensure users understand when and why authentication is required, while maintaining the educational and demo-friendly nature of the application.
