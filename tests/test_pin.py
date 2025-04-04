# tests/test_pin.py
import requests

def test_add_pinterest_data_endpoint():
    url = "http://127.0.0.1:5000/add-pinterest-data"
    payload = {
        "shoe_id": "674a2609f03d766411a9308b"
    }
    response = requests.post(url, json=payload)
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())
