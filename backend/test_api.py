"""
Simple test script for RecallLens API
"""
import requests
import json
from pathlib import Path


def test_health_check():
    """Test health check endpoint"""
    print("Testing health check...")
    response = requests.get("http://localhost:8000/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def test_analyze_endpoint():
    """Test analyze endpoint with sample image"""
    print("\nTesting /analyze endpoint...")

    # Create a simple test image if it doesn't exist
    import cv2
    import numpy as np

    test_image_path = Path("test_ad.jpg")
    if not test_image_path.exists():
        # Create a simple test image with text
        img = np.ones((400, 600, 3), dtype=np.uint8) * 255
        cv2.putText(img, "TEST AD", (150, 200), cv2.FONT_HERSHEY_BOLD, 3, (0, 0, 0), 5)
        cv2.imwrite(str(test_image_path), img)
        print(f"Created test image: {test_image_path}")

    # Prepare request
    url = "http://localhost:8000/analyze"
    files = {"file": open(test_image_path, "rb")}
    data = {
        "speed_kmh": 80,
        "view_distance_m": 30,
        "dwell_sec": 1.0,
        "lighting": "day",
        "phone_distraction": "low"
    }

    try:
        response = requests.post(url, files=files, data=data)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"\nJob ID: {result['job_id']}")
            print(f"Recall Score: {result['recall_score']:.2%}")
            print(f"Predicted Gist: {result['predicted_gist']}")
            print(f"Cognitive Load: {result['cognitive_load']:.2%}")
            print(f"Attention Score: {result['attention_score']:.2%}")
            print(f"\nArtifact URLs:")
            for name, url in result['artifact_urls'].items():
                print(f"  - {name}: {url}")
            print(f"\nSuggestions ({len(result['suggestions'])}):")
            for sug in result['suggestions'][:3]:
                print(f"  - [{sug['severity']}] {sug['issue']}")
        else:
            print(f"Error: {response.text}")

        return response.status_code == 200

    except Exception as e:
        print(f"Error: {str(e)}")
        return False
    finally:
        files["file"].close()


if __name__ == "__main__":
    print("=" * 60)
    print("RecallLens API Test Suite")
    print("=" * 60)

    print("\nMake sure the API is running:")
    print("  uvicorn app:app --reload")
    print()

    input("Press Enter when API is ready...")

    # Run tests
    health_ok = test_health_check()
    analyze_ok = test_analyze_endpoint()

    print("\n" + "=" * 60)
    print("Test Results:")
    print(f"  Health Check: {'✓ PASS' if health_ok else '✗ FAIL'}")
    print(f"  Analyze Endpoint: {'✓ PASS' if analyze_ok else '✗ FAIL'}")
    print("=" * 60)
