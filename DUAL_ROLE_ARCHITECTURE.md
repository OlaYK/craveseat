# Dual Role System Architecture

## System Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER SIGNUP                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   Create User    │
                    │ user_type="user" │
                    │ + UserProfile    │
                    └──────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │                                         │
        ▼                                         ▼
┌──────────────────┐                    ┌──────────────────┐
│  Stay as User    │                    │ Become Vendor    │
│                  │                    │ POST /vendor/    │
│ user_type="user" │                    └──────────────────┘
│ ✓ UserProfile    │                             │
│ ✗ VendorProfile  │                             ▼
└──────────────────┘              ┌──────────────────────────┐
                                  │   System Auto-Updates    │
                                  │ user_type="user"→"both"  │
                                  │ active_role="vendor"     │
                                  │ + VendorProfile created  │
                                  └──────────────────────────┘
                                             │
                                             ▼
                                  ┌──────────────────────┐
                                  │   Dual Role User     │
                                  │ user_type="both"     │
                                  │ ✓ UserProfile        │
                                  │ ✓ VendorProfile      │
                                  └──────────────────────┘
                                             │
                    ┌────────────────────────┴────────────────────────┐
                    │        POST /auth/switch-role                   │
                    │        {"target_role": "user" or "vendor"}      │
                    └────────────────────────┬────────────────────────┘
                                             │
                    ┌────────────────────────┴────────────────────────┐
                    │                                                 │
                    ▼                                                 ▼
        ┌──────────────────────┐                        ┌──────────────────────┐
        │    User Mode         │                        │    Vendor Mode       │
        │ active_role="user"   │                        │ active_role="vendor" │
        ├──────────────────────┤                        ├──────────────────────┤
        │ ✓ Browse cravings    │                        │ ✓ Manage profile     │
        │ ✓ Create cravings    │                        │ ✓ Add items          │
        │ ✓ View responses     │                        │ ✓ Upload images      │
        │ ✓ Update profile     │                        │ ✓ View analytics     │
        │ ✗ Vendor dashboard   │                        │ ✗ Create cravings    │
        └──────────────────────┘                        └──────────────────────┘
```

## Database Relationships

```
┌──────────────────────────────────────────────────────────────┐
│                         users                                 │
├──────────────────────────────────────────────────────────────┤
│ id (PK)                                                       │
│ username                                                      │
│ email                                                         │
│ user_type: ENUM('user', 'vendor', 'both')                    │
│ active_role: ENUM('user', 'vendor') NULLABLE                 │
│ ...                                                           │
└───────────────────┬──────────────────────┬───────────────────┘
                    │                      │
         ┌──────────┘                      └──────────┐
         │ 1:1                                    1:1 │
         ▼                                            ▼
┌─────────────────────┐                  ┌─────────────────────┐
│  user_profiles      │                  │  vendor_profiles    │
├─────────────────────┤                  ├─────────────────────┤
│ user_id (PK, FK)    │                  │ vendor_id (PK, FK)  │
│ bio                 │                  │ business_name       │
│ phone_number        │                  │ vendor_phone        │
│ delivery_address    │                  │ vendor_email        │
│ image_url           │                  │ logo_url            │
│ ...                 │                  │ banner_url          │
└─────────────────────┘                  │ rating              │
                                         │ ...                 │
                                         └──────────┬──────────┘
                                                    │ 1:N
                                                    ▼
                                         ┌─────────────────────┐
                                         │   vendor_items      │
                                         ├─────────────────────┤
                                         │ id (PK)             │
                                         │ vendor_id (FK)      │
                                         │ item_name           │
                                         │ item_price          │
                                         │ item_image_url      │
                                         │ ...                 │
                                         └─────────────────────┘
```

## Access Control Flow

```
┌─────────────────────────────────────────────────────────────────┐
│              Vendor Endpoint Request (e.g., GET /vendor/)        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────────┐
                    │ get_current_user()   │
                    │ (JWT validation)     │
                    └──────────────────────┘
                              │
                              ▼
                    ┌──────────────────────┐
                    │ require_vendor_role()│
                    └──────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────────┐
        │ Does user have vendor_profile?              │
        └─────────────────────────────────────────────┘
                │                           │
                │ NO                        │ YES
                ▼                           ▼
        ┌──────────────┐         ┌──────────────────────┐
        │ 403 Error    │         │ Is active_role       │
        │ "Create      │         │ set to 'vendor'?     │
        │  vendor      │         └──────────────────────┘
        │  profile"    │                   │
        └──────────────┘         ┌─────────┴─────────┐
                                 │ NO                │ YES
                                 ▼                   ▼
                        ┌──────────────┐    ┌──────────────┐
                        │ 403 Error    │    │ ✓ Allow      │
                        │ "Switch to   │    │   Access     │
                        │  vendor mode"│    └──────────────┘
                        └──────────────┘
```

## User Type State Machine

```
                    ┌──────────────────┐
                    │   Initial State  │
                    │   (Signup)       │
                    └────────┬─────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
        ┌──────────────┐          ┌──────────────┐
        │ user_type    │          │ user_type    │
        │ = "user"     │          │ = "vendor"   │
        └──────┬───────┘          └──────┬───────┘
               │                         │
               │ Create                  │ Create
               │ VendorProfile           │ UserProfile
               │                         │ (future)
               ▼                         ▼
        ┌──────────────────────────────────┐
        │      user_type = "both"          │
        │                                  │
        │  ┌────────────┐  ┌────────────┐ │
        │  │active_role │  │active_role │ │
        │  │= "user"    │  │= "vendor"  │ │
        │  └────────────┘  └────────────┘ │
        │         ▲              ▲         │
        │         │              │         │
        │         └──────┬───────┘         │
        │                │                 │
        │    POST /auth/switch-role        │
        └──────────────────────────────────┘
```

## API Endpoint Categories

```
┌─────────────────────────────────────────────────────────────────┐
│                    PUBLIC ENDPOINTS                              │
│  (No authentication required)                                    │
├─────────────────────────────────────────────────────────────────┤
│  POST /auth/signup                                               │
│  POST /auth/login                                                │
│  GET  /vendor/categories                                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                 AUTHENTICATED ENDPOINTS                          │
│  (Requires valid JWT token)                                      │
├─────────────────────────────────────────────────────────────────┤
│  GET  /auth/users/me                                             │
│  GET  /auth/current-role                                         │
│  POST /auth/switch-role                                          │
│  PUT  /auth/users/me/change-password                             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                  USER ROLE ENDPOINTS                             │
│  (Requires UserProfile + active_role="user")                     │
├─────────────────────────────────────────────────────────────────┤
│  GET  /user-profile/                                             │
│  PUT  /user-profile/                                             │
│  POST /user-profile/upload-image                                 │
│  GET  /cravings/                                                 │
│  POST /cravings/                                                 │
│  ... (other user features)                                       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                 VENDOR ROLE ENDPOINTS                            │
│  (Requires VendorProfile + active_role="vendor")                 │
├─────────────────────────────────────────────────────────────────┤
│  POST /vendor/                    (Create - any user can do)     │
│  GET  /vendor/                    (Requires vendor role)         │
│  PUT  /vendor/                    (Requires vendor role)         │
│  POST /vendor/upload-logo         (Requires vendor role)         │
│  POST /vendor/upload-banner       (Requires vendor role)         │
│  POST /vendor/items               (Requires vendor role)         │
│  GET  /vendor/items               (Requires vendor role)         │
│  POST /vendor/items/{id}/upload-image  (Requires vendor role)    │
│  DELETE /vendor/items/{id}        (Requires vendor role)         │
└─────────────────────────────────────────────────────────────────┘
```

## Example User Scenarios

### Scenario A: Food Lover → Restaurant Owner
```
Day 1: Sarah signs up as a user
  ├─ user_type: "user"
  ├─ UserProfile: ✓
  └─ VendorProfile: ✗

Day 30: Sarah opens a restaurant and creates vendor profile
  ├─ user_type: "user" → "both" (auto-updated)
  ├─ active_role: "vendor" (auto-set)
  ├─ UserProfile: ✓
  └─ VendorProfile: ✓ (newly created)

Day 31: Sarah wants to browse other restaurants
  ├─ POST /auth/switch-role {"target_role": "user"}
  ├─ active_role: "vendor" → "user"
  └─ Can now browse as a regular user

Day 32: Sarah wants to update her restaurant menu
  ├─ POST /auth/switch-role {"target_role": "vendor"}
  ├─ active_role: "user" → "vendor"
  └─ Can now manage vendor profile and items
```

### Scenario B: Restaurant Owner → Food Enthusiast
```
Day 1: Mike signs up as a vendor
  ├─ user_type: "vendor"
  ├─ UserProfile: ✓ (auto-created during signup)
  ├─ VendorProfile: ✗ (needs to create)
  └─ active_role: "user" (default)

Day 2: Mike creates vendor profile
  ├─ POST /vendor/ {...}
  ├─ user_type: "vendor" → "vendor" (stays same)
  ├─ active_role: "vendor" (auto-set)
  └─ VendorProfile: ✓ (newly created)

Day 3: Mike wants to order food from other vendors
  ├─ POST /auth/switch-role {"target_role": "user"}
  ├─ active_role: "vendor" → "user"
  └─ Can browse and create cravings
```

---

## Key Takeaways

1. **Flexible System**: Users can start as either role and upgrade later
2. **Automatic Upgrades**: Creating a vendor profile auto-upgrades user_type to "both"
3. **Role Switching**: Simple API call to switch between user and vendor modes
4. **Access Control**: Endpoints check both profile existence and active role
5. **No Data Loss**: Switching roles doesn't delete or hide any data
6. **Seamless UX**: Users can be both consumers and providers on the platform
