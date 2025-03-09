import requests

BASE_URL = "http://mlstatstracker.org/api"

def test_create_batch_success():
    payload = {
        "name": "batch1",
        "xCoordinates": [1.1, 2.2, 3.3],
        "yCoordinates": [4.4, 5.5, 6.6]
    }
    response = requests.post(f"{BASE_URL}/batch", json=payload)
    # Expecting a 201 Created on success
    assert response.status_code == 201
    data = response.json()
    assert "runId" in data

def test_create_batch_missing_fields():
    payload = {"name": "batch1"}  # Missing coordinates
    response = requests.post(f"{BASE_URL}/batch", json=payload)
    # Validation error should return 400 Bad Request
    assert response.status_code == 400
    data = response.json()
    assert "error" in data

def test_create_batch_invalid_coordinates():
    payload = {
        "name": "batch_invalid",
        "xCoordinates": ["invalid", 2.2, 3.3],
        "yCoordinates": [4.4, 5.5, "bad_data"]
    }
    response = requests.post(f"{BASE_URL}/batch", json=payload)
    # Validation error should return 400 Bad Request
    assert response.status_code == 400
    data = response.json()
    assert "error" in data

def test_query_batch_success():
    payload = {"query_name": "batch1"}
    response = requests.post(f"{BASE_URL}/query", json=payload)
    # A found batch should return 200 OK
    assert response.status_code == 200
    data = response.json()
    # Assuming the API returns a structured JSON object with coordinates and a runId
    assert "xCoordinates" in data
    assert "yCoordinates" in data

def test_query_batch_not_found():
    payload = {"query_name": "non_existent_batch"}
    response = requests.post(f"{BASE_URL}/query", json=payload)
    # Not found should return 404 Not Found
    assert response.status_code == 404
    data = response.json()
    assert "error" in data

def test_query_batch_empty_name():
    payload = {"query_name": ""}
    response = requests.post(f"{BASE_URL}/query", json=payload)
    # Invalid query should return 400 Bad Request
    assert response.status_code == 400
    data = response.json()
    assert "error" in data

