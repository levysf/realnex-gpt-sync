# Simple script to debug RealNex API 415 errors
# Run this locally to test different approaches

import requests
import json
import os

# Your credentials
REALNEX_API_TOKEN = "YOUR_API_KEY_HERE"  # Replace with your actual key
REALNEX_SELECTED_DB = "YOUR_DB_KEY_HERE"  # Replace with your actual db key
TEST_CONTACT_KEY = "YOUR_TEST_CONTACT_KEY"  # Replace with actual contact key

REALNEX_API_BASE = "https://sync.realnex.com/api/v1"

def test_contact_update(contact_key: str):
    """Test different methods to update a contact"""
    url = f"{REALNEX_API_BASE}/Crm/contact/{contact_key}/investor"
    
    # Test minimal payload
    minimal_payload = {
        "userFields": {
            "user3": "test_value"
        }
    }
    
    print(f"Testing contact: {contact_key}")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(minimal_payload, indent=2)}")
    print("-" * 50)
    
    # Test 1: Basic JSON
    headers1 = {
        "Authorization": f"Bearer {REALNEX_API_TOKEN}",
        "Content-Type": "application/json",
        "X-SelectedDb-Key": REALNEX_SELECTED_DB
    }
    
    print("Test 1: Basic JSON with PUT")
    try:
        response = requests.put(url, json=minimal_payload, headers=headers1)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        print(f"Response Headers: {dict(response.headers)}")
    except Exception as e:
        print(f"Error: {e}")
    print("-" * 30)
    
    # Test 2: POST instead of PUT
    print("Test 2: Basic JSON with POST")
    try:
        response = requests.post(url, json=minimal_payload, headers=headers1)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    print("-" * 30)
    
    # Test 3: Form data
    headers2 = {
        "Authorization": f"Bearer {REALNEX_API_TOKEN}",
        "Content-Type": "application/x-www-form-urlencoded", 
        "X-SelectedDb-Key": REALNEX_SELECTED_DB
    }
    
    form_data = {
        "userFields.user3": "test_value"
    }
    
    print("Test 3: Form data")
    try:
        response = requests.put(url, data=form_data, headers=headers2)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    print("-" * 30)
    
    # Test 4: OPTIONS request to see what's allowed
    headers3 = {
        "Authorization": f"Bearer {REALNEX_API_TOKEN}",
        "X-SelectedDb-Key": REALNEX_SELECTED_DB
    }
    
    print("Test 4: OPTIONS request")
    try:
        response = requests.options(url, headers=headers3)
        print(f"Status: {response.status_code}")
        print(f"Allow header: {response.headers.get('Allow', 'Not specified')}")
        print(f"All headers: {dict(response.headers)}")
    except Exception as e:
        print(f"Error: {e}")
    print("-" * 30)

if __name__ == "__main__":
    if REALNEX_API_TOKEN == "YOUR_API_KEY_HERE":
        print("Please update the credentials at the top of this script!")
    else:
        test_contact_update(TEST_CONTACT_KEY)
