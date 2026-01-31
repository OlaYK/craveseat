# Create new file: authentication/role_helpers.py

from fastapi import HTTPException, status
from authentication.models import User, UserType


def require_vendor_role(current_user: User):
    """
    Check if user is currently in vendor mode or has vendor access
    Raises 403 if not
    """
    # Get the active role (defaults to user_type if active_role is not set)
    active_role = current_user.active_role or current_user.user_type
    
    # Check if user has vendor profile
    has_vendor_profile = bool(current_user.vendor_profile)
    
    # Allow access if:
    # 1. User type is vendor (pure vendor account)
    # 2. User type is both AND active role is vendor
    # 3. User has a vendor profile (for backward compatibility)
    if (current_user.user_type == UserType.vendor or 
        (current_user.user_type == UserType.both and active_role == UserType.vendor) or
        (has_vendor_profile and active_role == UserType.vendor)):
        return True
    
    # If user has vendor profile but isn't in vendor mode, suggest switching
    if has_vendor_profile:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please switch to vendor mode using /auth/switch-role to access vendor features"
        )
    
    # User doesn't have vendor access at all
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You need to create a vendor profile first. Visit /vendor to set up your vendor profile."
    )



def require_user_role(current_user: User):
    """
    Check if user is currently in user mode
    Raises 403 if not
    """
    active_role = current_user.active_role or current_user.user_type
    
    if active_role != UserType.user and current_user.user_type != UserType.user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires user access. Switch to user mode using /auth/switch-role"
        )
    
    return True


def get_active_role(current_user: User) -> UserType:
    """
    Get the current active role of the user
    """
    return current_user.active_role or current_user.user_type


def can_access_vendor_features(current_user: User) -> bool:
    """
    Check if user can access vendor features (has vendor profile)
    """
    return bool(current_user.vendor_profile)


def can_access_user_features(current_user: User) -> bool:
    """
    Check if user can access user features (has user profile)
    """
    return bool(current_user.profile)