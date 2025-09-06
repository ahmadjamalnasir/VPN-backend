#!/usr/bin/env python3
"""
Test script for Prime VPN API with proper request parameters
"""
import requests
import json
from uuid import uuid4

BASE_URL = "http://localhost:8000"

def test_proper_apis():
    print("🧪 Testing Prime VPN API with Proper Request Parameters")
    print("=" * 60)
    
    # Test user registration
    print("1. Testing user registration...")
    email = f"test_{uuid4().hex[:8]}@example.com"
    user_data = {
        "email": email,
        "password": "testpassword123"
    }
    response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=user_data)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        user = response.json()
        print(f"   User created: {user['email']}")
        user_id = user['id']
    else:
        print(f"   Error: {response.text}")
        return
    print()
    
    # Test user login
    print("2. Testing user login...")
    login_data = {
        "email": email,
        "password": "testpassword123"
    }
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        login_result = response.json()
        print(f"   Login successful, token: {login_result['access_token'][:20]}...")
    else:
        print(f"   Error: {response.text}")
    print()
    
    # Test user lookup by email
    print("3. Testing user lookup by email...")
    response = requests.get(f"{BASE_URL}/api/v1/users/profile?email={email}")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        user_profile = response.json()
        print(f"   Found user: {user_profile['email']}")
    else:
        print(f"   Error: {response.text}")
    print()
    
    # Test subscription creation
    print("4. Testing subscription creation...")
    response = requests.post(
        f"{BASE_URL}/api/v1/subscriptions/create?user_email={email}&plan_type=monthly"
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        subscription = response.json()
        print(f"   Subscription created: {subscription['plan_type']} - {subscription['status']}")
    else:
        print(f"   Error: {response.text}")
    print()
    
    # Test get subscription by email
    print("5. Testing get subscription by user email...")
    response = requests.get(f"{BASE_URL}/api/v1/subscriptions/user?email={email}")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        subscription = response.json()
        print(f"   Subscription: {subscription['plan_type']} expires {subscription['end_date']}")
    else:
        print(f"   Error: {response.text}")
    print()
    
    # Test VPN servers
    print("6. Testing VPN servers with location filter...")
    response = requests.get(f"{BASE_URL}/api/v1/vpn/servers?location=us-east")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        servers = response.json()
        print(f"   Found {len(servers)} servers in us-east")
    else:
        print(f"   Error: {response.text}")
    print()
    
    # Test VPN connection
    print("7. Testing VPN connection...")
    connect_data = {
        "client_public_key": "test_public_key_12345",
        "location": "us-east"
    }
    response = requests.post(
        f"{BASE_URL}/api/v1/vpn/connect?user_email={email}",
        json=connect_data
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        connection = response.json()
        print(f"   Connected to server: {connection['server']['hostname']}")
        print(f"   Client IP: {connection['client_ip']}")
        connection_id = connection['connection_id']
    else:
        print(f"   Error: {response.text}")
        connection_id = None
    print()
    
    # Test get user connections
    print("8. Testing get user connections...")
    response = requests.get(f"{BASE_URL}/api/v1/vpn/connections?user_email={email}")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        connections = response.json()
        print(f"   User has {len(connections)} connections")
    else:
        print(f"   Error: {response.text}")
    print()
    
    # Test VPN disconnect
    if connection_id:
        print("9. Testing VPN disconnect...")
        response = requests.post(
            f"{BASE_URL}/api/v1/vpn/disconnect?connection_id={connection_id}&user_email={email}&bytes_sent=1048576&bytes_received=2097152"
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            disconnection = response.json()
            print(f"   Disconnected. Total bytes: {disconnection['bytes_sent'] + disconnection['bytes_received']}")
        else:
            print(f"   Error: {response.text}")
        print()

if __name__ == "__main__":
    try:
        test_proper_apis()
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure it's running on localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")