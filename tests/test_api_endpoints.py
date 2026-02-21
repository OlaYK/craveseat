import os
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


os.environ["DATABASE_URL"] = "sqlite://"
os.environ["GOOGLE_CLIENT_ID"] = "test-google-client-id"

from database import Base, get_db  # noqa: E402
from main import app  # noqa: E402
from vendor_profile.models import ServiceCategory  # noqa: E402
import authentication.auth as auth_routes  # noqa: E402
import cravings.routes as cravings_routes  # noqa: E402
import user_profile.routes as user_profile_routes  # noqa: E402
import vendor_profile.routes as vendor_profile_routes  # noqa: E402


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _signup(client: TestClient, username: str, email: str, phone: str, password: str = "Password123!") -> tuple[str, str]:
    response = client.post(
        "/auth/signup",
        json={
            "username": username,
            "email": email,
            "full_name": username.title(),
            "password": password,
            "confirm_password": password,
            "phone_number": phone,
            "delivery_address": "123 Testing Road",
            "bio": "test bio",
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()["data"]
    return payload["access_token"], payload["user"]["id"]


def _login(client: TestClient, email_or_username: str, password: str) -> str:
    response = client.post(
        "/auth/login",
        json={"email_or_username": email_or_username, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]["access_token"]


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch):
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(test_engine, "connect")
    def _register_sqlite_functions(dbapi_connection, _connection_record):
        dbapi_connection.create_function("now", 0, lambda: datetime.utcnow().isoformat(" "))

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    db = TestingSessionLocal()
    db.add(ServiceCategory(name="Food", description="Food vendors"))
    db.commit()
    db.close()

    def override_get_db():
        db_session = TestingSessionLocal()
        try:
            yield db_session
        finally:
            db_session.close()

    async def fake_upload_image(file, folder: str = "uploads"):
        return f"https://cdn.test/{folder}/{file.filename}"

    def fake_verify_google_token(_id_token: str) -> dict:
        return {
            "email": "google.user@example.com",
            "email_verified": True,
            "name": "Google User",
            "iss": "accounts.google.com",
        }

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(user_profile_routes, "upload_image", fake_upload_image)
    monkeypatch.setattr(vendor_profile_routes, "upload_image", fake_upload_image)
    monkeypatch.setattr(cravings_routes, "upload_image", fake_upload_image)
    monkeypatch.setattr(auth_routes, "_verify_google_id_token", fake_verify_google_token)

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_all_endpoints_smoke(client: TestClient):
    assert client.get("/").status_code == 200
    assert client.get("/health").status_code == 200

    token_1, user_1_id = _signup(client, "owner", "owner@example.com", "+12345678901")
    token_2, user_2_id = _signup(client, "responder", "responder@example.com", "+12345678902")

    token_from_token_endpoint = client.post(
        "/auth/token",
        json={"email_or_username": "owner", "password": "Password123!"},
    )
    assert token_from_token_endpoint.status_code == 200
    assert token_from_token_endpoint.json()["token_type"] == "bearer"

    me_response = client.get("/auth/users/me", headers=_auth_header(token_1))
    assert me_response.status_code == 200
    assert me_response.json()["data"]["username"] == "owner"

    by_id_response = client.get(f"/auth/users/{user_1_id}", headers=_auth_header(token_1))
    assert by_id_response.status_code == 200
    assert by_id_response.json()["data"]["id"] == user_1_id

    current_role_response = client.get("/auth/current-role", headers=_auth_header(token_1))
    assert current_role_response.status_code == 200
    assert current_role_response.json()["data"]["active_role"] == "user"

    profile_get_response = client.get("/profile/", headers=_auth_header(token_1))
    assert profile_get_response.status_code == 200

    profile_username_update = client.patch(
        "/profile/",
        json={"username": "owner_updated"},
        headers=_auth_header(token_1),
    )
    assert profile_username_update.status_code == 200, profile_username_update.text
    assert profile_username_update.json()["data"]["username"] == "owner_updated"

    old_username_login = client.post(
        "/auth/login",
        json={"email_or_username": "owner", "password": "Password123!"},
    )
    assert old_username_login.status_code == 401

    token_1 = _login(client, "owner_updated", "Password123!")

    profile_single_field_update = client.patch(
        "/profile/",
        json={"bio": "Updated bio only"},
        headers=_auth_header(token_1),
    )
    assert profile_single_field_update.status_code == 200
    assert profile_single_field_update.json()["data"]["bio"] == "Updated bio only"

    profile_upload_image = client.post(
        "/profile/upload-image",
        headers=_auth_header(token_1),
        files={"file": ("profile.jpg", b"fake-image-bytes", "image/jpeg")},
    )
    assert profile_upload_image.status_code == 200
    assert "cdn.test/user_profiles/profile.jpg" in profile_upload_image.json()["data"]["image_url"]

    auth_change_password = client.put(
        "/auth/users/me/change-password",
        json={"old_password": "Password123!", "new_password": "Password123!A"},
        headers=_auth_header(token_1),
    )
    assert auth_change_password.status_code == 200
    token_1 = _login(client, "owner_updated", "Password123!A")

    profile_change_password = client.post(
        "/profile/change-password",
        json={"old_password": "Password123!A", "new_password": "Password123!B"},
        headers=_auth_header(token_1),
    )
    assert profile_change_password.status_code == 200
    token_1 = _login(client, "owner_updated", "Password123!B")

    categories_response = client.get("/vendor/categories", headers=_auth_header(token_1))
    assert categories_response.status_code == 200
    category_id = categories_response.json()["data"][0]["id"]

    create_vendor_profile = client.post(
        "/vendor/",
        json={
            "business_name": "Owner Foods",
            "service_category_id": category_id,
            "vendor_address": "1 Vendor Road",
            "vendor_phone": "+12345678901",
            "vendor_email": "owner.vendor@example.com",
        },
        headers=_auth_header(token_1),
    )
    assert create_vendor_profile.status_code == 200, create_vendor_profile.text

    get_vendor_profile = client.get("/vendor/", headers=_auth_header(token_1))
    assert get_vendor_profile.status_code == 200

    update_vendor_profile = client.put(
        "/vendor/",
        json={"business_name": "Owner Foods Updated"},
        headers=_auth_header(token_1),
    )
    assert update_vendor_profile.status_code == 200
    assert update_vendor_profile.json()["data"]["business_name"] == "Owner Foods Updated"

    upload_logo = client.post(
        "/vendor/upload-logo",
        headers=_auth_header(token_1),
        files={"file": ("logo.png", b"fake-logo", "image/png")},
    )
    assert upload_logo.status_code == 200
    assert "cdn.test/vendor_logos/logo.png" in upload_logo.json()["data"]["logo_url"]

    upload_banner = client.post(
        "/vendor/upload-banner",
        headers=_auth_header(token_1),
        files={"file": ("banner.png", b"fake-banner", "image/png")},
    )
    assert upload_banner.status_code == 200
    assert "cdn.test/vendor_banners/banner.png" in upload_banner.json()["data"]["banner_url"]

    add_item = client.post(
        "/vendor/items",
        json={
            "item_name": "Jollof Rice",
            "item_description": "Spicy rice",
            "item_price": "18.50",
            "availability_status": "available",
        },
        headers=_auth_header(token_1),
    )
    assert add_item.status_code == 200
    item_id = add_item.json()["data"]["id"]

    list_items = client.get("/vendor/items", headers=_auth_header(token_1))
    assert list_items.status_code == 200
    assert len(list_items.json()["data"]) == 1

    upload_item_image = client.post(
        f"/vendor/items/{item_id}/upload-image",
        headers=_auth_header(token_1),
        files={"file": ("item.png", b"fake-item", "image/png")},
    )
    assert upload_item_image.status_code == 200
    assert "cdn.test/vendor_items/item.png" in upload_item_image.json()["data"]["item_image_url"]

    switch_to_user = client.post(
        "/auth/switch-role",
        json={"target_role": "user"},
        headers=_auth_header(token_1),
    )
    assert switch_to_user.status_code == 200
    assert switch_to_user.json()["data"]["active_role"] == "user"

    create_craving = client.post(
        "/cravings/",
        json={
            "name": "Need Pizza",
            "description": "Large pepperoni pizza",
            "category": "food",
            "anonymous": False,
            "delivery_address": "123 Testing Road",
            "recommended_vendor": "Pizza Hub",
            "vendor_link": "https://vendor.example/pizza-hub",
            "notes": "Extra cheese",
        },
        headers=_auth_header(token_1),
    )
    assert create_craving.status_code == 201, create_craving.text
    craving_data = create_craving.json()["data"]
    craving_id = craving_data["id"]
    assert craving_data["name"] == "Need Pizza"
    assert craving_data["vendor_link"] == "https://vendor.example/pizza-hub"

    list_cravings = client.get("/cravings/", headers=_auth_header(token_1))
    assert list_cravings.status_code == 200
    assert len(list_cravings.json()["data"]) == 1

    list_my_cravings = client.get("/cravings/my-cravings", headers=_auth_header(token_1))
    assert list_my_cravings.status_code == 200
    assert len(list_my_cravings.json()["data"]) == 1

    get_single_craving = client.get(f"/cravings/{craving_id}", headers=_auth_header(token_1))
    assert get_single_craving.status_code == 200

    share_url_response = client.get(f"/cravings/{craving_id}/share-url", headers=_auth_header(token_1))
    assert share_url_response.status_code == 200
    share_token = share_url_response.json()["data"]["share_token"]

    upload_craving_image = client.post(
        f"/cravings/{craving_id}/upload-image",
        headers=_auth_header(token_1),
        files={"file": ("craving.png", b"fake-craving", "image/png")},
    )
    assert upload_craving_image.status_code == 200
    assert "cdn.test/cravings/craving.png" in upload_craving_image.json()["data"]["image_url"]

    update_craving = client.put(
        f"/cravings/{craving_id}",
        json={
            "name": "Need Burger",
            "vendor_link": "https://vendor.example/burger",
        },
        headers=_auth_header(token_1),
    )
    assert update_craving.status_code == 200
    assert update_craving.json()["data"]["name"] == "Need Burger"

    public_craving_view = client.get(f"/public/craving/{share_token}")
    assert public_craving_view.status_code == 200

    public_profile = client.get(f"/public/profile/{user_1_id}")
    assert public_profile.status_code == 200
    assert public_profile.json()["data"]["username"] == "owner_updated"

    create_response = client.post(
        f"/responses/?craving_id={craving_id}",
        json={"message": "I can deliver in 20 minutes"},
        headers=_auth_header(token_2),
    )
    assert create_response.status_code == 201, create_response.text
    response_id = create_response.json()["data"]["id"]

    list_craving_responses = client.get(f"/responses/craving/{craving_id}", headers=_auth_header(token_1))
    assert list_craving_responses.status_code == 200
    assert len(list_craving_responses.json()["data"]) == 1

    list_my_responses = client.get("/responses/my-responses", headers=_auth_header(token_2))
    assert list_my_responses.status_code == 200
    assert len(list_my_responses.json()["data"]) == 1

    get_response = client.get(f"/responses/{response_id}", headers=_auth_header(token_2))
    assert get_response.status_code == 200

    update_response_message = client.put(
        f"/responses/{response_id}",
        json={"message": "Updated delivery offer"},
        headers=_auth_header(token_2),
    )
    assert update_response_message.status_code == 200

    update_response_status = client.put(
        f"/responses/{response_id}",
        json={"status": "accepted"},
        headers=_auth_header(token_1),
    )
    assert update_response_status.status_code == 200
    assert update_response_status.json()["data"]["status"] == "accepted"

    notifications_list = client.get("/notifications/", headers=_auth_header(token_1))
    assert notifications_list.status_code == 200
    assert len(notifications_list.json()["data"]) >= 1
    notification_id = notifications_list.json()["data"][0]["id"]

    unread_count = client.get("/notifications/unread-count", headers=_auth_header(token_1))
    assert unread_count.status_code == 200

    mark_read = client.post(
        "/notifications/mark-read",
        json={"notification_ids": [notification_id]},
        headers=_auth_header(token_1),
    )
    assert mark_read.status_code == 200

    mark_all_read = client.post("/notifications/mark-all-read", headers=_auth_header(token_1))
    assert mark_all_read.status_code == 200

    delete_notification = client.delete(f"/notifications/{notification_id}", headers=_auth_header(token_1))
    assert delete_notification.status_code == 200

    anonymous_public_response = client.post(
        f"/public/craving/{share_token}/respond",
        json={"message": "Anonymous answer", "is_anonymous": True},
    )
    assert anonymous_public_response.status_code == 200
    assert anonymous_public_response.json()["data"]["is_anonymous"] is True

    delete_response = client.delete(f"/responses/{response_id}", headers=_auth_header(token_2))
    assert delete_response.status_code == 200

    delete_craving = client.delete(f"/cravings/{craving_id}", headers=_auth_header(token_1))
    assert delete_craving.status_code == 200

    switch_to_vendor = client.post(
        "/auth/switch-role",
        json={"target_role": "vendor"},
        headers=_auth_header(token_1),
    )
    assert switch_to_vendor.status_code == 200
    assert switch_to_vendor.json()["data"]["active_role"] == "vendor"

    delete_item = client.delete(f"/vendor/items/{item_id}", headers=_auth_header(token_1))
    assert delete_item.status_code == 200

    google_signup_or_login = client.post(
        "/auth/google",
        json={"id_token": "fake-google-token", "phone_number": "+12345678903"},
    )
    assert google_signup_or_login.status_code == 200
    assert google_signup_or_login.json()["data"]["is_new_user"] is True

    google_login_existing = client.post(
        "/auth/google",
        json={"id_token": "fake-google-token"},
    )
    assert google_login_existing.status_code == 200
    assert google_login_existing.json()["data"]["is_new_user"] is False

    # Ensure both users created at the beginning are still retrievable.
    assert client.get(f"/public/profile/{user_2_id}").status_code == 200
