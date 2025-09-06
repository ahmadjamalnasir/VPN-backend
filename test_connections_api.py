#!/usr/bin/env python3
"""
Test user connections API with session stats
"""
import requests
import json
from uuid import uuid4

BASE_URL = "http://localhost:8000"

def test_connections_api():
    print("🧪 Testing User Connections API")
    print("=" * 40)
    
    # Use existing user or create new one
    email = "test@example.com"  # Replace with actual user email
    
    # Test get user connections
    print("1. Testing get user connections...")
    response = requests.get(f"{BASE_URL}/api/v1/users/connections?email={email}&limit=10")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        sessions = response.json()
        print(f"   Found {len(sessions)} connection sessions")
        if sessions:
            session = sessions[0]
            print(f"   Latest session:")
            print(f"     Server: {session['server_hostname']} ({session['server_location']})")
            print(f"     Duration: {session['duration_formatted']}")
            print(f"     Data: {session['total_bytes']} bytes")
            print(f"     Avg Speed: {session['avg_speed_mbps']} MB/s")
            print(f"     Status: {session['status']}")
    else:
        print(f"   Error: {response.text}")
    print()
    
    # Test get user connection stats
    print("2. Testing get user connection stats...")
    response = requests.get(f"{BASE_URL}/api/v1/users/connections/stats?email={email}")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        stats = response.json()
        print(f"   Overall Statistics:")
        print(f"     Total Sessions: {stats['total_sessions']}")
        print(f"     Total Data: {stats['total_data_gb']} GB")
        print(f"     Avg Session Duration: {stats['avg_session_duration_seconds']} seconds")
        print(f"     Avg Session Data: {stats['avg_session_data_mb']} MB")
    else:
        print(f"   Error: {response.text}")
    print()
    
    # Test filter by status
    print("3. Testing filter connections by status...")
    response = requests.get(f"{BASE_URL}/api/v1/users/connections?email={email}&status=disconnected&limit=5")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        sessions = response.json()
        print(f"   Found {len(sessions)} disconnected sessions")
    else:
        print(f"   Error: {response.text}")

if __name__ == "__main__":
    try:
        test_connections_api()
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure it's running on localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")