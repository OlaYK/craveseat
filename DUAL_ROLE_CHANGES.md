# Dual Role System - Changes Summary

## Question
**Can a user have both user and vendor profiles and switch between them?**

## Answer
**YES!** The system already had this capability built-in, but there were bugs preventing it from working. All issues have been fixed.

---

## Changes Made

### 1. Fixed `authentication/auth.py`
**Problem:** Missing imports for `VendorProfile` and `UserProfile` models  
**Solution:** Added imports at the top of the file

```python
from vendor_profile.models import VendorProfile
from user_profile.models import UserProfile
```

**Impact:** The `/auth/switch-role` endpoint can now properly check if users have the required profiles.

---

### 2. Updated `authentication/role_helpers.py`
**Problem:** `require_vendor_role()` only checked `user_type`, blocking users with `user_type="both"`  
**Solution:** Rewrote the function to properly support dual-role users

**Old Logic:**
```python
if active_role != UserType.vendor and current_user.user_type != UserType.vendor:
    raise HTTPException(...)
```

**New Logic:**
```python
# Allow access if:
# 1. User type is vendor (pure vendor account)
# 2. User type is both AND active role is vendor
# 3. User has a vendor profile AND active role is vendor
if (current_user.user_type == UserType.vendor or 
    (current_user.user_type == UserType.both and active_role == UserType.vendor) or
    (has_vendor_profile and active_role == UserType.vendor)):
    return True
```

**Impact:** Users with both profiles can now access vendor features when in vendor mode.

---

### 3. Updated `vendor_profile/routes.py`
**Problem:** All endpoints checked `if current_user.user_type != UserType.vendor`, blocking dual-role users  
**Solution:** 
1. Added import: `from authentication.role_helpers import require_vendor_role`
2. Replaced all `user_type` checks with `require_vendor_role(current_user)`
3. Updated `create_vendor_profile` to allow any user to become a vendor

**Endpoints Updated:**
- ✅ `POST /vendor/` - Create vendor profile
- ✅ `GET /vendor/` - Get vendor profile
- ✅ `PUT /vendor/` - Update vendor profile
- ✅ `POST /vendor/upload-logo` - Upload logo
- ✅ `POST /vendor/upload-banner` - Upload banner
- ✅ `POST /vendor/items` - Add item
- ✅ `GET /vendor/items` - List items
- ✅ `POST /vendor/items/{item_id}/upload-image` - Upload item image
- ✅ `DELETE /vendor/items/{item_id}` - Delete item

**Special Enhancement in `create_vendor_profile`:**
```python
# Update user to have both roles if they only had user role
if current_user.user_type == UserType.user:
    current_user.user_type = UserType.both
    current_user.active_role = UserType.vendor
    db.commit()
```

**Impact:** 
- Any user can now create a vendor profile
- System automatically upgrades them to dual-role status
- All vendor endpoints now respect the active role

---

## How It Works Now

### User Journey: Regular User → Dual Role
1. User signs up → Gets `UserProfile`, `user_type="user"`
2. User creates vendor profile via `POST /vendor/`
3. System automatically:
   - Creates `VendorProfile`
   - Changes `user_type` to `"both"`
   - Sets `active_role` to `"vendor"`
4. User can now switch between roles using `POST /auth/switch-role`

### Role Switching
```http
POST /auth/switch-role
{
  "target_role": "vendor"  // or "user"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully switched to vendor mode",
  "data": {
    "active_role": "vendor",
    "user_type": "both",
    "has_user_profile": true,
    "has_vendor_profile": true
  }
}
```

### Access Control
- **Vendor endpoints:** Check if user has vendor profile AND is in vendor mode
- **User endpoints:** Check if user has user profile (and optionally user mode)
- **Error messages:** Guide users to switch roles or create missing profiles

---

## Testing Recommendations

### Test 1: Create Vendor Profile as User
```bash
# 1. Sign up as user
POST /auth/signup
{
  "username": "testuser",
  "email": "test@example.com",
  "password": "password123",
  "confirm_password": "password123",
  "phone_number": "+1234567890",
  "user_type": "user"
}

# 2. Create vendor profile
POST /vendor/
{
  "business_name": "Test Business",
  "service_category_id": 1,
  "vendor_phone": "+1234567890"
}

# 3. Check current role
GET /auth/current-role
# Should show: user_type="both", active_role="vendor"
```

### Test 2: Switch Roles
```bash
# Switch to user mode
POST /auth/switch-role
{
  "target_role": "user"
}

# Try to access vendor endpoint (should fail)
GET /vendor/
# Error: "Please switch to vendor mode"

# Switch back to vendor mode
POST /auth/switch-role
{
  "target_role": "vendor"
}

# Access vendor endpoint (should succeed)
GET /vendor/
```

### Test 3: Access Control
```bash
# User without vendor profile tries to switch
POST /auth/switch-role
{
  "target_role": "vendor"
}
# Error: "You must create a vendor profile before switching to vendor mode"
```

---

## Files Modified

1. ✅ `authentication/auth.py` - Added imports
2. ✅ `authentication/role_helpers.py` - Fixed role checking logic
3. ✅ `vendor_profile/routes.py` - Updated all endpoints to use role-based access
4. ✅ `DUAL_ROLE_GUIDE.md` - Created comprehensive documentation

---

## No Database Changes Required

The database schema already supports dual roles:
- ✅ `UserType` enum has `"both"` option
- ✅ `active_role` field exists in User model
- ✅ User can have both `profile` and `vendor_profile` relationships

**No migrations needed!** Just restart your server to apply the code changes.

---

## Summary

**Before:** Users were locked into their initial role choice  
**After:** Users can seamlessly switch between user and vendor roles

**What was broken:**
1. ❌ Missing imports
2. ❌ Incorrect role checking logic
3. ❌ Vendor endpoints blocked dual-role users

**What's fixed:**
1. ✅ All imports added
2. ✅ Smart role checking that supports dual-role users
3. ✅ All vendor endpoints work with role switching
4. ✅ Automatic upgrade to dual-role when creating vendor profile

**Your dual-role system is now fully operational!** 🚀
