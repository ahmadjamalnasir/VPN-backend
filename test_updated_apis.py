#!/usr/bin/env python3
"""
Test updated APIs with all new features
"""
import requests
import json
from uuid import uuid4

BASE_URL = "http://localhost:8000"

def test_complete_flow():
    print("🧪 Testing Updated Prime VPN APIs")
    print("=" * 50)
    
    # Test user signup
    print("1. Testing user signup...")
    email = f"test_{uuid4().hex[:8]}@example.com"
    signup_data = {
        "name": "Test User",
        "email": email,
        "password": "testpassword123",
        "phone": "+1234567890",
        "country": "US"
    }
    response = requests.post(f"{BASE_URL}/api/v1/auth/signup", json=signup_data)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        user = response.json()
        print(f"   User created: {user['name']} (ID: {user['user_id']})")
        user_id = user['user_id']
    else:
        print(f"   Error: {response.text}")
        return
    print()
    
    # Test email verification (simulate OTP)
    print("2. Testing email verification...")
    verify_data = {
        "email": email,
        "otp_code": "123456"  # In real scenario, get from email
    }
    response = requests.post(f"{BASE_URL}/api/v1/auth/verify-email", json=verify_data)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text}")
    print()
    
    # Test login
    print("3. Testing login...")
    login_data = {
        "email": email,
        "password": "testpassword123"
    }
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        login_result = response.json()
        print(f"   Login successful: User ID {login_result['user_id']}, Premium: {login_result['is_premium']}")
    else:
        print(f"   Error: {response.text}")
    print()
    
    # Test get subscription plans
    print("4. Testing subscription plans...")
    response = requests.get(f"{BASE_URL}/api/v1/subscriptions/plans")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        plans = response.json()
        print(f"   Found {len(plans)} plans:")
        for plan in plans:
            print(f"     Plan {plan['plan_id']}: {plan['name']} - ${plan['price']}")
    print()
    
    # Test assign subscription
    print("5. Testing subscription assignment...")
    assign_data = {
        "user_email": email,
        "plan_id": 2  # Monthly premium
    }
    response = requests.post(f"{BASE_URL}/api/v1/subscriptions/assign", json=assign_data)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        subscription = response.json()
        print(f"   Subscription assigned: {subscription['plan']['name']}")
    else:
        print(f"   Error: {response.text}")
    print()
    
    # Test VPN servers with premium filter
    print("6. Testing VPN servers (premium)...")
    response = requests.get(f"{BASE_URL}/api/v1/vpn/servers?is_premium=true")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        servers = response.json()
        print(f"   Found {len(servers)} premium servers")
    print()
    
    # Test VPN connection
    print("7. Testing VPN connection...")
    connect_data = {
        "client_public_key": "test_premium_key_12345",
        "location": "us-east"
    }
    response = requests.post(
        f"{BASE_URL}/api/v1/vpn/connect?user_email={email}",
        json=connect_data
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        connection = response.json()
        print(f"   Connected to: {connection['server']['hostname']}")
        print(f"   Server premium: {connection['server']['is_premium']}")
        connection_id = connection['connection_id']
    else:
        print(f"   Error: {response.text}")
        connection_id = None
    print()
    
    # Test user update
    print("8. Testing user update...")
    update_data = {
        "name": "Updated Test User",
        "phone": "+9876543210"
    }
    response = requests.put(
        f"{BASE_URL}/api/v1/users/update?email={email}",
        json=update_data
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        updated_user = response.json()
        print(f"   Updated name: {updated_user['name']}")
    print()
    
    # Test VPN disconnect with duration
    if connection_id:
        print("9. Testing VPN disconnect...")
        response = requests.post(
            f"{BASE_URL}/api/v1/vpn/disconnect?connection_id={connection_id}&user_email={email}&bytes_sent=5242880&bytes_received=10485760"
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            disconnection = response.json()
            print(f"   Disconnected. Duration: {disconnection['duration_seconds']} seconds")
            print(f"   Total data: {disconnection['bytes_sent'] + disconnection['bytes_received']} bytes")
        print()

if __name__ == "__main__":
    try:
        test_complete_flow()
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure it's running on localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")