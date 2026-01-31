# Dual Role System Guide (User & Vendor)

## Overview
Your CraveSeat application **fully supports** users having both user and vendor profiles simultaneously. Users can switch between roles seamlessly based on what they want to do.

---

## How It Works

### User Types
The system has three user types defined in `authentication/models.py`:
- **`user`** - Regular user (can browse and create cravings)
- **`vendor`** - Vendor only (can manage vendor profile and items)
- **`both`** - Has both user and vendor capabilities

### Active Role
Users with `user_type="both"` have an `active_role` field that determines which features they can currently access:
- When `active_role="user"` → Access user features
- When `active_role="vendor"` → Access vendor features

---

## User Journey Examples

### Scenario 1: User Becomes a Vendor
1. **Sign up** as a regular user → Gets `UserProfile` automatically
2. **Create vendor profile** via `POST /vendor/` → System automatically:
   - Creates `VendorProfile`
   - Updates `user_type` from `user` to `both`
   - Sets `active_role` to `vendor`
3. **Switch roles** anytime using `POST /auth/switch-role`

### Scenario 2: Vendor Wants to Browse as User
1. Vendor with `user_type="vendor"` creates a vendor profile
2. To browse as a user, they need a `UserProfile` (currently not auto-created for vendors)
3. Once they have both profiles, they can switch between roles

---

## API Endpoints

### Role Management

#### Check Current Role
```http
GET /auth/current-role
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "active_role": "user",
    "user_type": "both",
    "has_user_profile": true,
    "has_vendor_profile": true,
    "can_switch_to_vendor": true,
    "can_switch_to_user": true
  }
}
```

#### Switch Role
```http
POST /auth/switch-role
Authorization: Bearer <token>
Content-Type: application/json

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

**Error Cases:**
- Switching to vendor without vendor profile → 400 error with message to create profile
- Switching to user without user profile → 400 error

---

### Creating Profiles

#### Create Vendor Profile (Any User Can Do This)
```http
POST /vendor/
Authorization: Bearer <token>
Content-Type: application/json

{
  "business_name": "Joe's Pizza",
  "service_category_id": 1,
  "vendor_address": "123 Main St",
  "vendor_phone": "+1234567890",
  "vendor_email": "joe@pizza.com"
}
```

**What Happens:**
- Creates vendor profile
- If user had `user_type="user"`, it's upgraded to `both`
- Sets `active_role="vendor"`

---

## Access Control

### Vendor Endpoints
All vendor endpoints now use `require_vendor_role()` which checks:
1. Does user have a vendor profile?
2. Is their active role set to vendor?

**Affected Endpoints:**
- `GET /vendor/` - Get vendor profile
- `PUT /vendor/` - Update vendor profile
- `POST /vendor/upload-logo` - Upload logo
- `POST /vendor/upload-banner` - Upload banner
- `POST /vendor/items` - Add item
- `GET /vendor/items` - List items
- `POST /vendor/items/{item_id}/upload-image` - Upload item image
- `DELETE /vendor/items/{item_id}` - Delete item

**Error Messages:**
- If not in vendor mode but has profile: *"Please switch to vendor mode using /auth/switch-role"*
- If no vendor profile: *"You need to create a vendor profile first"*

---

## Database Schema

### User Table
```sql
users:
  - id (PK)
  - username
  - email
  - user_type (ENUM: 'user', 'vendor', 'both')
  - active_role (ENUM: 'user', 'vendor', NULL)
  - ... other fields
```

### Relationships
```
User (1) ←→ (0..1) UserProfile
User (1) ←→ (0..1) VendorProfile
```

A single user can have:
- Only UserProfile (regular user)
- Only VendorProfile (vendor only)
- **Both profiles** (dual-role user) ✅

---

## Frontend Implementation Tips

### 1. Show Role Switcher
If `user_type === "both"`, show a toggle/dropdown to switch roles:
```javascript
if (userData.user_type === "both") {
  // Show role switcher UI
  // Current role: userData.active_role
}
```

### 2. Conditional Navigation
```javascript
// Show vendor dashboard link only if has vendor profile
if (userData.has_vendor_profile) {
  showVendorDashboardLink();
}

// Show user features if has user profile
if (userData.has_user_profile) {
  showUserFeatures();
}
```

### 3. Handle Role Switching
```javascript
async function switchRole(targetRole) {
  const response = await fetch('/auth/switch-role', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ target_role: targetRole })
  });
  
  if (response.ok) {
    // Refresh user data and update UI
    await fetchCurrentUser();
  }
}
```

### 4. Upgrade to Vendor Flow
```javascript
async function becomeVendor(vendorData) {
  const response = await fetch('/vendor/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(vendorData)
  });
  
  if (response.ok) {
    // User is now a vendor!
    // They'll be automatically switched to vendor mode
    await fetchCurrentUser();
  }
}
```

---

## Testing the Dual Role System

### Test Case 1: User Upgrades to Vendor
1. Sign up as user
2. Create vendor profile
3. Verify `user_type` changed to `both`
4. Verify `active_role` is `vendor`
5. Access vendor endpoints successfully

### Test Case 2: Switch Between Roles
1. User with both profiles
2. Switch to vendor mode
3. Access vendor endpoints ✅
4. Try to access user-only features (should work based on profile)
5. Switch back to user mode
6. Access user features ✅

### Test Case 3: Access Control
1. User in "user" mode tries to access vendor endpoint
2. Should get error: "Please switch to vendor mode"
3. User without vendor profile tries to switch to vendor
4. Should get error: "Create vendor profile first"

---

## Known Limitations & Future Enhancements

### Current Limitations
1. **Vendors can't automatically get UserProfile** - If someone signs up as vendor, they don't get a UserProfile automatically (only VendorProfile)
2. **No endpoint to create UserProfile for existing vendors** - Vendors can't "downgrade" to become dual-role users

### Recommended Enhancements
1. **Auto-create UserProfile for vendors** - When vendor signs up, create both profiles
2. **Add endpoint to create UserProfile** - Allow vendors to create user profile
3. **Role-based UI components** - Show different navigation based on active role
4. **Role history/analytics** - Track when users switch roles

---

## Summary

✅ **YES**, users can have both user and vendor profiles!  
✅ **YES**, they can switch between roles seamlessly!  
✅ **The system is already built** - just needed the fixes applied above!

The key changes made:
1. ✅ Fixed imports in `auth.py`
2. ✅ Updated `require_vendor_role()` to support dual-role users
3. ✅ Changed all vendor endpoints to use role-based access control
4. ✅ Made vendor profile creation open to all users (auto-upgrades them)

**Your dual-role system is now fully functional!** 🎉
