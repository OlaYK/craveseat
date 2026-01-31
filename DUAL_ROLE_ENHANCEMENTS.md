# Dual Role System - Future Enhancements

## Current Gaps & Recommended Improvements

### 1. Vendor-to-User Profile Creation ⚠️

**Current Issue:**
- Users who sign up as "user" get a `UserProfile` automatically ✅
- Users who sign up as "vendor" do NOT get a `UserProfile` automatically ❌
- Vendors can't easily become dual-role users

**Recommendation:**
Create an endpoint to allow vendors to create a user profile:

```python
# Add to user_profile/routes.py

@router.post("/", response_model=schemas.UserProfileResponse)
def create_user_profile(
    profile: schemas.UserProfileCreate,
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    """Create user profile - allows vendors to become dual-role users"""
    # Check if user profile already exists
    existing_profile = crud.get_user_profile(db, current_user.id)
    if existing_profile:
        raise HTTPException(status_code=400, detail="User profile already exists.")
    
    # Create the user profile
    new_profile = crud.create_user_profile(db, current_user.id, profile)
    
    # Update user to have both roles if they only had vendor role
    if current_user.user_type == UserType.vendor:
        current_user.user_type = UserType.both
        current_user.active_role = UserType.user
        db.commit()
    
    return new_profile
```

---

### 2. Auto-Create Both Profiles on Signup 💡

**Current Behavior:**
- User signup → Only `UserProfile` created
- Vendor signup → Only `UserProfile` created (no `VendorProfile`)

**Recommended Behavior:**
Option A: Ask during signup if they want to be a vendor too
Option B: Always create both profiles (lightweight approach)
Option C: Keep current system but make it clearer

**Implementation (Option A - Recommended):**

```python
# Update authentication/schemas.py

class UserCreate(UserBase):
    password: str
    confirm_password: str
    # Profile fields
    bio: Optional[str] = None
    phone_number: str
    delivery_address: Optional[str] = None
    
    # NEW: Optional vendor fields during signup
    also_vendor: bool = False  # "Do you also want to sell food?"
    business_name: Optional[str] = None
    vendor_phone: Optional[str] = None
    service_category_id: Optional[int] = None

# Update authentication/crud.py

def create_user_with_profiles(db: Session, user: schemas.UserCreate):
    """Create user with both profiles if requested"""
    from user_profile.models import UserProfile
    from vendor_profile.models import VendorProfile
    
    hashed_password = get_password_hash(user.password)
    
    # Determine user type
    user_type = UserType.both if user.also_vendor else UserType.user
    
    # Create user
    db_user = models.User(
        username=user.username.lower(),
        email=user.email.lower(),
        full_name=user.full_name,
        hashed_password=hashed_password,
        user_type=user_type,
        active_role=UserType.vendor if user.also_vendor else UserType.user,
        disabled=False,
    )
    db.add(db_user)
    db.flush()
    
    # Always create user profile
    db_profile = UserProfile(
        user_id=db_user.id,
        bio=user.bio,
        phone_number=user.phone_number,
        delivery_address=user.delivery_address,
    )
    db.add(db_profile)
    
    # Optionally create vendor profile
    if user.also_vendor:
        db_vendor_profile = VendorProfile(
            vendor_id=db_user.id,
            business_name=user.business_name,
            vendor_phone=user.vendor_phone or user.phone_number,
            service_category_id=user.service_category_id,
        )
        db.add(db_vendor_profile)
    
    db.commit()
    db.refresh(db_user)
    return db_user
```

---

### 3. Role-Based UI Components 🎨

**Frontend Enhancement:**
Create reusable components that show/hide based on active role

```javascript
// React example
function RoleBasedNav({ user }) {
  const isVendor = user.active_role === 'vendor';
  const isUser = user.active_role === 'user';
  const hasBothRoles = user.user_type === 'both';
  
  return (
    <nav>
      {/* Always show */}
      <Link to="/profile">Profile</Link>
      
      {/* Show only in user mode */}
      {isUser && (
        <>
          <Link to="/browse">Browse Food</Link>
          <Link to="/my-cravings">My Cravings</Link>
        </>
      )}
      
      {/* Show only in vendor mode */}
      {isVendor && (
        <>
          <Link to="/vendor-dashboard">Dashboard</Link>
          <Link to="/vendor/items">My Items</Link>
          <Link to="/vendor/analytics">Analytics</Link>
        </>
      )}
      
      {/* Show role switcher if user has both roles */}
      {hasBothRoles && (
        <RoleSwitcher currentRole={user.active_role} />
      )}
    </nav>
  );
}

function RoleSwitcher({ currentRole }) {
  const switchRole = async (targetRole) => {
    await fetch('/auth/switch-role', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getToken()}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ target_role: targetRole })
    });
    window.location.reload(); // Or update state
  };
  
  return (
    <div className="role-switcher">
      <span>Mode: {currentRole}</span>
      <button onClick={() => switchRole(currentRole === 'user' ? 'vendor' : 'user')}>
        Switch to {currentRole === 'user' ? 'Vendor' : 'User'} Mode
      </button>
    </div>
  );
}
```

---

### 4. Role History & Analytics 📊

**Track Role Switching:**
Add a table to track when users switch roles

```python
# Create new model: authentication/models.py

class RoleSwitch(Base):
    __tablename__ = "role_switches"
    
    id = Column(String, primary_key=True, default=shortuuid.uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    from_role = Column(Enum(UserType), nullable=False)
    to_role = Column(Enum(UserType), nullable=False)
    switched_at = Column(TIMESTAMP, server_default=text("now()"), nullable=False)
    
    user = relationship("User", backref="role_switches")
```

**Analytics Endpoint:**

```python
# Add to authentication/auth.py

@router.get("/role-analytics")
def get_role_analytics(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's role switching history and stats"""
    switches = db.query(RoleSwitch).filter(
        RoleSwitch.user_id == current_user.id
    ).order_by(RoleSwitch.switched_at.desc()).limit(10).all()
    
    return {
        "success": True,
        "data": {
            "current_role": current_user.active_role.value,
            "user_type": current_user.user_type.value,
            "total_switches": len(switches),
            "recent_switches": [
                {
                    "from": s.from_role.value,
                    "to": s.to_role.value,
                    "when": s.switched_at
                }
                for s in switches
            ]
        }
    }
```

---

### 5. Permissions & Fine-Grained Access Control 🔐

**Current System:**
- Binary: Either full vendor access or no vendor access
- No granular permissions

**Enhancement:**
Add permission levels for vendors

```python
# vendor_profile/models.py

class VendorPermission(PyEnum):
    view_profile = "view_profile"
    edit_profile = "edit_profile"
    add_items = "add_items"
    edit_items = "edit_items"
    delete_items = "delete_items"
    view_analytics = "view_analytics"
    manage_staff = "manage_staff"  # Future: multi-user vendor accounts

class VendorRole(Base):
    __tablename__ = "vendor_roles"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)  # e.g., "owner", "manager", "staff"
    permissions = Column(JSON)  # List of VendorPermission values

# Then check permissions in endpoints
def require_vendor_permission(permission: VendorPermission):
    def decorator(current_user: User):
        require_vendor_role(current_user)
        # Check if user has specific permission
        # (Implementation depends on how you store permissions)
        return True
    return decorator
```

---

### 6. Notification System for Role Changes 🔔

**Notify users when:**
- They successfully create a vendor profile
- They switch roles
- They gain new capabilities

```python
# Add to authentication/auth.py

@router.post("/switch-role")
def switch_role(
    target_role: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    # ... existing code ...
    
    # Create notification
    from notifications.crud import create_notification
    
    create_notification(
        db=db,
        user_id=current_user.id,
        title=f"Switched to {target_role} mode",
        message=f"You are now in {target_role} mode. You can switch back anytime.",
        notification_type="role_change"
    )
    
    return {
        "success": True,
        "message": f"Successfully switched to {target_role} mode",
        # ... rest of response
    }
```

---

### 7. Onboarding Flow for New Vendors 🎓

**Create a guided setup process:**

```python
# vendor_profile/routes.py

@router.get("/onboarding-status")
def get_vendor_onboarding_status(
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    """Check vendor profile completion status"""
    require_vendor_role(current_user)
    
    profile = crud.get_vendor_profile(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Vendor profile not found")
    
    # Check completion
    steps = {
        "profile_created": True,
        "business_name_set": bool(profile.business_name),
        "category_selected": bool(profile.service_category_id),
        "logo_uploaded": bool(profile.logo_url),
        "banner_uploaded": bool(profile.banner_url),
        "first_item_added": len(profile.items) > 0,
        "phone_verified": False,  # Future: phone verification
        "email_verified": False,  # Future: email verification
    }
    
    completed = sum(steps.values())
    total = len(steps)
    
    return {
        "success": True,
        "data": {
            "completion_percentage": (completed / total) * 100,
            "steps": steps,
            "next_step": get_next_onboarding_step(steps)
        }
    }

def get_next_onboarding_step(steps):
    """Determine what the vendor should do next"""
    if not steps["business_name_set"]:
        return "Set your business name"
    if not steps["category_selected"]:
        return "Choose your service category"
    if not steps["logo_uploaded"]:
        return "Upload your logo"
    if not steps["first_item_added"]:
        return "Add your first item"
    return "All set! Start receiving orders"
```

---

### 8. Prevent Accidental Role Confusion 🚨

**Add confirmation dialogs:**

```javascript
// Frontend: Confirm before switching roles
async function switchRoleWithConfirmation(targetRole) {
  const currentRole = getCurrentRole();
  
  const message = targetRole === 'vendor'
    ? 'Switch to vendor mode? You will be able to manage your business.'
    : 'Switch to user mode? You will be able to browse and order food.';
  
  if (confirm(message)) {
    await switchRole(targetRole);
  }
}

// Show warning if user tries to access wrong features
function checkRoleBeforeAction(requiredRole, action) {
  const currentRole = getCurrentRole();
  
  if (currentRole !== requiredRole) {
    alert(`This action requires ${requiredRole} mode. Switch roles first.`);
    return false;
  }
  
  return action();
}
```

---

### 9. Bulk Operations for Dual-Role Users 🔄

**Allow users to perform actions in both roles:**

```python
# Example: Get all activity (both as user and vendor)

@router.get("/my-activity")
def get_all_activity(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Get combined activity from both user and vendor roles"""
    activity = []
    
    # User activity
    if current_user.profile:
        cravings = db.query(Craving).filter(
            Craving.user_id == current_user.id
        ).all()
        activity.extend([
            {"type": "craving", "data": c, "role": "user"}
            for c in cravings
        ])
    
    # Vendor activity
    if current_user.vendor_profile:
        items = db.query(VendorItem).filter(
            VendorItem.vendor_id == current_user.id
        ).all()
        activity.extend([
            {"type": "item", "data": i, "role": "vendor"}
            for i in items
        ])
    
    # Sort by date
    activity.sort(key=lambda x: x["data"].created_at, reverse=True)
    
    return {
        "success": True,
        "data": activity
    }
```

---

### 10. Role-Based Dashboard 📈

**Create a unified dashboard that shows different content based on role:**

```python
@router.get("/dashboard")
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Get role-specific dashboard data"""
    active_role = current_user.active_role or current_user.user_type
    
    if active_role == UserType.vendor:
        # Vendor dashboard
        profile = crud.get_vendor_profile(db, current_user.id)
        items = crud.get_vendor_items(db, current_user.id)
        
        return {
            "success": True,
            "role": "vendor",
            "data": {
                "profile": profile,
                "total_items": len(items),
                "active_items": len([i for i in items if i.availability_status == AvailabilityStatus.available]),
                "rating": profile.rating,
                "verification_status": profile.verification_status.value
            }
        }
    else:
        # User dashboard
        cravings = db.query(Craving).filter(
            Craving.user_id == current_user.id
        ).all()
        
        return {
            "success": True,
            "role": "user",
            "data": {
                "total_cravings": len(cravings),
                "active_cravings": len([c for c in cravings if c.status == "active"]),
                "favorite_vendors": []  # Future: track favorites
            }
        }
```

---

## Priority Recommendations

### High Priority 🔴
1. **Vendor-to-User Profile Creation** - Fill the gap for vendors who want to become users
2. **Role-Based UI Components** - Essential for good UX
3. **Onboarding Flow** - Help new vendors get started

### Medium Priority 🟡
4. **Auto-Create Both Profiles** - Simplify signup process
5. **Notification System** - Keep users informed
6. **Role-Based Dashboard** - Improve user experience

### Low Priority 🟢
7. **Role History & Analytics** - Nice to have for insights
8. **Permissions System** - Only needed for complex vendor setups
9. **Bulk Operations** - Convenience feature
10. **Accidental Role Confusion Prevention** - UX polish

---

## Implementation Timeline

### Phase 1 (Week 1)
- ✅ Fix current dual-role bugs (DONE!)
- 🔲 Add vendor-to-user profile creation endpoint
- 🔲 Create basic role switcher UI component

### Phase 2 (Week 2)
- 🔲 Implement onboarding flow for vendors
- 🔲 Add role-based navigation components
- 🔲 Create unified dashboard

### Phase 3 (Week 3)
- 🔲 Add notification system for role changes
- 🔲 Implement role history tracking
- 🔲 Add analytics endpoints

### Phase 4 (Future)
- 🔲 Fine-grained permissions system
- 🔲 Multi-user vendor accounts
- 🔲 Advanced analytics and reporting

---

## Conclusion

The dual-role system is now **fully functional**, but these enhancements would make it even better! Prioritize based on your users' needs and feedback.
