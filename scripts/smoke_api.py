# test_api_endpoints.py
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_health_endpoint():
    """Test health check endpoint."""
    print("\n[1] Testing Health Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.json()}")
        assert response.status_code == 200
        print(f"  ✓ Health endpoint working")
        return True
    except Exception as e:
        print(f"  ✗ Health endpoint failed: {e}")
        return False

def test_analyze_endpoint():
    """Test emotion analysis endpoint."""
    print("\n[2] Testing Analyze Endpoint...")
    try:
        data = {
            "text": "I'm feeling really happy and excited about today!"
        }
        response = requests.post(f"{BASE_URL}/api/v1/analyze", json=data)
        print(f"  Status: {response.status_code}")
        result = response.json()
        
        print(f"  Top Emotion: {result.get('top_emotion')}")
        print(f"  Confidence: {result.get('top_confidence'):.1%}")
        print(f"  Intensity:  {result.get('emotional_intensity'):.1f}/10")
        
        assert response.status_code == 200
        assert 'top_emotion' in result
        assert 'emotional_intensity' in result
        print(f"  ✓ Analyze endpoint working")
        return True
    except Exception as e: 
        print(f"  ✗ Analyze endpoint failed:  {e}")
        return False

def test_journal_create():
    """Test journal entry creation."""
    print("\n[3] Testing Journal Create Endpoint...")
    try:
        data = {
            "content": "Today was amazing! I got promoted at work and I'm so grateful!",
            "user_id": 1  # Adjust based on your user setup
        }
        response = requests.post(f"{BASE_URL}/api/v1/journal", json=data)
        print(f"  Status: {response. status_code}")
        
        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            print(f"  Entry ID: {result.get('id')}")
            print(f"  Emotion: {result.get('emotion')}")
            print(f"  ✓ Journal create working")
            return True, result. get('id')
        else:
            print(f"  Response: {response.json()}")
            return False, None
    except Exception as e:
        print(f"  ✗ Journal create failed: {e}")
        return False, None

def test_journal_list(user_id=1):
    """Test journal entry listing."""
    print("\n[4] Testing Journal List Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/journal? user_id={user_id}")
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"  Entries found: {len(result) if isinstance(result, list) else 'N/A'}")
            print(f"  ✓ Journal list working")
            return True
        else:
            print(f"  Response: {response. json()}")
            return False
    except Exception as e:
        print(f"  ✗ Journal list failed: {e}")
        return False

def test_journal_get(entry_id):
    """Test getting a specific journal entry."""
    print(f"\n[5] Testing Journal Get Endpoint (ID: {entry_id})...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/journal/{entry_id}")
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"  Entry emotion: {result.get('emotion')}")
            print(f"  ✓ Journal get working")
            return True
        else: 
            print(f"  Response: {response.json()}")
            return False
    except Exception as e:
        print(f"  ✗ Journal get failed: {e}")
        return False

def run_all_api_tests():
    """Run all API tests in sequence."""
    print("=" * 80)
    print("BACKEND API TESTING")
    print("=" * 80)
    print(f"\nBase URL: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # Test health
    results.append(("Health Check", test_health_endpoint()))
    
    # Test analyze
    results.append(("Analyze Endpoint", test_analyze_endpoint()))
    
    # Test journal endpoints
    success, entry_id = test_journal_create()
    results.append(("Journal Create", success))
    
    if entry_id:
        results.append(("Journal Get", test_journal_get(entry_id)))
    
    results.append(("Journal List", test_journal_list()))
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    for test_name, passed in results: 
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name: <30} {status}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\nTotal:  {passed}/{total} tests passed")
    print("=" * 80)

if __name__ == "__main__": 
    # Make sure your FastAPI server is running! 
    print("\n⚠ Make sure your FastAPI server is running on http://localhost:8000")
    input("Press Enter to continue...")
    
    run_all_api_tests()