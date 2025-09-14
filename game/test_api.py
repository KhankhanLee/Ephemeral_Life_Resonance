#!/usr/bin/env python3
import requests
import json
import time

def test_health():
    """헬스 체크 테스트"""
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"Health check: {response.status_code} - {response.json()}")
        return True
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_ai():
    """AI API 테스트"""
    payload = {
        "npc": "jisu",
        "scene_id": "test",
        "state": {"day": 1, "stress": 5},
        "memory": []
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/ai",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        print(f"AI API: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print(f"Error: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"AI API test failed: {e}")
        return False

if __name__ == "__main__":
    print("=== API 테스트 시작 ===")
    
    if test_health():
        print("\n=== AI API 테스트 ===")
        test_ai()
    else:
        print("서버가 실행되지 않고 있습니다. 먼저 'python3 server.py'를 실행해주세요.")
