"""
Test script to verify phone number validation during signup
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_signup_without_phone():
    """Test that signup fails without phone number"""
    print("\n1. Testing signup WITHOUT phone number (should fail)...")
    
    data = {
        "username": "testuser1",
        "email": "test1@example.com",
        "password": "password123",
        "confirm_password": "password123",
        "full_name": "Test User"
    }
    
    response = requests.post(f"{BASE_URL}/auth/signup", json=data)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 422, "Should fail validation without phone number"
    print("   ✓ Correctly rejected signup without phone number")


def test_signup_with_invalid_phone():
    """Test that signup fails with invalid phone number"""
    print("\n2. Testing signup with INVALID phone number (should fail)...")
    
    invalid_phones = [
        "123",  # Too short
        "abc123456789",  # Contains letters
        "12345678901234567890",  # Too long
    ]
    
    for phone in invalid_phones:
        data = {
            "username": f"testuser_{phone}",
            "email": f"test_{phone}@example.com",
            "password": "password123",
            "confirm_password": "password123",
            "full_name": "Test User",
            "phone_number": phone
        }
        
        response = requests.post(f"{BASE_URL}/auth/signup", json=data)
        print(f"   Phone: {phone}")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        assert response.status_code == 422, f"Should fail validation for phone: {phone}"
        print(f"   ✓ Correctly rejected invalid phone: {phone}")


def test_signup_with_valid_phone():
    """Test that signup succeeds with valid phone number"""
    print("\n3. Testing signup with VALID phone numbers (should succeed)...")
    
    valid_phones = [
        "+1234567890",
        "123-456-7890",
        "(123) 456-7890",
        "+44 20 7946 0958",
        "1234567890",
    ]
    
    for idx, phone in enumerate(valid_phones):
        data = {
            "username": f"validuser{idx}",
            "email": f"valid{idx}@example.com",
            "password": "password123",
            "confirm_password": "password123",
            "full_name": "Valid User",
            "phone_number": phone
        }
        
        response = requests.post(f"{BASE_URL}/auth/signup", json=data)
        print(f"   Phone: {phone}")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   Response: User created with ID: {response.json().get('id')}")
            print(f"   ✓ Successfully created user with phone: {phone}")
        else:
            print(f"   Response: {response.json()}")
            # Might fail if user already exists, which is okay for testing
            if "already registered" in str(response.json()):
                print(f"   ⚠ User already exists (this is okay for testing)")
            else:
                print(f"   ✗ Failed to create user with valid phone: {phone}")


if __name__ == "__main__":
    print("=" * 60)
    print("Phone Number Validation Test Suite")
    print("=" * 60)
    
    try:
        test_signup_without_phone()
        test_signup_with_invalid_phone()
        test_signup_with_valid_phone()
        
        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
