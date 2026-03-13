"""
Test script for AFAS API endpoints.

This script demonstrates how to test all API endpoints.
Run this after starting the server.
"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8001"
API_BASE = f"{BASE_URL}/api/v1"


def test_health_check():
    """Test health check endpoint."""
    print("\n=== Testing Health Check ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    print("✅ Health check passed")


def test_root():
    """Test root endpoint."""
    print("\n=== Testing Root Endpoint ===")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    print("✅ Root endpoint passed")


def test_create_submit():

    print("\n=== Testing Create Submit ===")

    submit_data = {
        "user_id": 11,
        "audio_path": "C:\\Users\\ADMIN\\Downloads\\11.mp3",
        "asr_type": "whisper"
    }


    response = requests.post(
        f"{API_BASE}/submit/",
        json=submit_data
    )

    print(f"Status Code: {response.status_code}")
    if response.status_code == 201:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        print("✅ Create submit passed")
    else:
        print(f"Error: {response.text}")



def test_get_submit(submit_id: int = 1):
    """Test getting submits for a submission."""
    print("\n=== Testing Get Submits ===")
    
    response = requests.get(f"{API_BASE}/submit/{submit_id}")
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        transcripts = response.json()
        print(f"Found {len(transcripts)} submit entries")
        if transcripts:
            print(f"First entry: {json.dumps(transcripts[0], indent=2)}")
        print("✅ Get submit passed")
    else:
        print(f"Error: {response.text}")


def test_create_transcript():
    """Test creating a transcript entry."""
    print("\n=== Testing Create Transcript ===")
    
    transcript_data = {
        "submit_id": 1,
        "word_index": 0,
        "word": "hello",
        "prob": 0.95,
        "start": 0.0,
        "end": 0.5
    }
    
    response = requests.post(
        f"{API_BASE}/transcripts/",
        json=transcript_data
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 201:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        print("✅ Create transcript passed")
        return response.json()["id"]
    else:
        print(f"Error: {response.text}")
        return None


def test_get_transcripts(submit_id: int = 1):
    """Test getting transcripts for a submission."""
    print("\n=== Testing Get Transcripts ===")
    
    response = requests.get(f"{API_BASE}/transcripts/{submit_id}")
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        transcripts = response.json()
        print(f"Found {len(transcripts)} transcript entries")
        if transcripts:
            print(f"First entry: {json.dumps(transcripts[0], indent=2)}")
        print("✅ Get transcripts passed")
    else:
        print(f"Error: {response.text}")


def test_create_fluency():
    """Test creating fluency metrics."""
    print("\n=== Testing Create Fluency ===")
    
    fluency_data = {
        "submit_id": 1,
        "speed_rate": 2.5,
        "pause_ratio": 0.15
    }
    
    response = requests.post(
        f"{API_BASE}/fluency/",
        json=fluency_data
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 201:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        print("✅ Create fluency passed")
    else:
        print(f"Error: {response.text}")


def test_get_fluency(submit_id: int = 1):
    """Test getting fluency metrics."""
    print("\n=== Testing Get Fluency ===")
    
    response = requests.get(f"{API_BASE}/fluency/{submit_id}")
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        print("✅ Get fluency passed")
    else:
        print(f"Error: {response.text}")


def test_create_lexical():
    """Test creating lexical metrics."""
    print("\n=== Testing Create Lexical ===")
    
    lexical_data = {
        "submit_id": 1,
        "ttr": 0.75,
        "mttr": 0.82,
        "A1": 20.0,
        "A2": 30.0,
        "B1": 25.0,
        "B2": 15.0,
        "C1": 10.0
    }
    
    response = requests.post(
        f"{API_BASE}/lexical/",
        json=lexical_data
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 201:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        print("✅ Create lexical passed")
    else:
        print(f"Error: {response.text}")


def test_get_lexical(submit_id: int = 1):
    """Test getting lexical metrics."""
    print("\n=== Testing Get Lexical ===")
    
    response = requests.get(f"{API_BASE}/lexical/{submit_id}")
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        print("✅ Get lexical passed")
    else:
        print(f"Error: {response.text}")


def test_create_pronunciation():
    """Test creating pronunciation metrics."""
    print("\n=== Testing Create Pronunciation ===")
    
    pronunciation_data = {
        "submit_id": 1,
        "score_0_50": 5.0,
        "score_50_70": 10.0,
        "score_70_85": 20.0,
        "score_85_95": 30.0,
        "score_95_100": 35.0
    }
    
    response = requests.post(
        f"{API_BASE}/pronunciation/",
        json=pronunciation_data
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 201:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        print("✅ Create pronunciation passed")
    else:
        print(f"Error: {response.text}")


def test_get_pronunciation(submit_id: int = 1):
    """Test getting pronunciation metrics."""
    print("\n=== Testing Get Pronunciation ===")
    
    response = requests.get(f"{API_BASE}/pronunciation/{submit_id}")
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        print("✅ Get pronunciation passed")
    else:
        print(f"Error: {response.text}")


def test_analytics():
    """Test analytics endpoints."""
    print("\n=== Testing Analytics ===")
    
    # Most fluent user
    print("\n--- Most Fluent User ---")
    response = requests.get(f"{API_BASE}/analytics/most-fluent-user")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Best lexical user
    print("\n--- Best Lexical User ---")
    response = requests.get(f"{API_BASE}/analytics/best-lexical-user")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Best pronunciation user
    print("\n--- Best Pronunciation User ---")
    response = requests.get(f"{API_BASE}/analytics/best-pronunciation-user")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    print("✅ Analytics tests passed")


def run_all_tests():
    """Run all API tests."""
    print("=" * 50)
    print("AFAS API Test Suite")
    print("=" * 50)
    print("\n⚠️  Make sure the server is running at http://localhost:8000")
    print("=" * 50)
    
    try:
        # Basic endpoints
        test_health_check()
        test_root()

        #Submit endpoints
        test_create_submit()
        test_get_submit()
        
        # Transcript endpoints
        test_create_transcript()
        test_get_transcripts(1)
        
        # Fluency endpoints
        test_create_fluency()
        test_get_fluency(1)
        
        # Lexical endpoints
        test_create_lexical()
        test_get_lexical(1)
        
        # Pronunciation endpoints
        test_create_pronunciation()
        test_get_pronunciation(1)
        
        # Analytics endpoints
        test_analytics()
        
        print("\n" + "=" * 50)
        print("✅ All tests completed!")
        print("=" * 50)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to server!")
        print("Please make sure the server is running:")
        print("  python -m uvicorn src.main:app --reload")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    run_all_tests()

