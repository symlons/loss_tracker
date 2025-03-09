import requests

BASE_URL = "http://mlstatstracker.org/api"

def test_create_batch_success():
    # Valid data for creating a batch
    payload = {"name": "batch1", "xCoordinates": [1.1, 2.2, 3.3], "yCoordinates": [4.4, 5.5, 6.6]}
    response = requests.post(f"{BASE_URL}/batch", json=payload)
    # Expecting a 201 Created response
    assert response.status_code == 201
    data = response.json()
    assert "runId" in data  # Ensure that 'runId' is returned

def test_create_batch_missing_fields():
    # Missing xCoordinates and yCoordinates
    payload = {"name": "batch1"}
    response = requests.post(f"{BASE_URL}/batch", json=payload)
    # Expecting a 400 Bad Request
    assert response.status_code == 400
    data = response.json()
    assert "error" in data  # Ensure an error message is returned

def test_create_batch_invalid_coordinates():
    # Invalid coordinates in the payload
    payload = {
        "name": "batch_invalid", 
        "xCoordinates": ["invalid", 2.2, 3.3],  # Invalid data type
        "yCoordinates": [4.4, 5.5, "bad_data"]  # Invalid data type
    }
    response = requests.post(f"{BASE_URL}/batch", json=payload)
    # Expecting a 400 Bad Request
    assert response.status_code == 400
    data = response.json()
    assert "error" in data  # Ensure an error message is returned

def test_query_batch_success():
    # Querying an existing batch
    payload = {"query_name": "batch1"}
    response = requests.post(f"{BASE_URL}/query", json=payload)
    # Expecting a 200 OK response
    assert response.status_code == 200
    data = response.json()

    # Ensure that 'points' is in the first item of the response
    assert "points" in data[0]

    # Ensure 'x' and 'y' are in the 'points' array of the first batch
    assert "x" in data[0]["points"][0]
    assert "y" in data[0]["points"][0]

def test_query_batch_not_found():
    # Querying a non-existent batch
    payload = {"query_name": "non_existent_batch"}
    response = requests.post(f"{BASE_URL}/query", json=payload)
    # Expecting a 404 Not Found response
    assert response.status_code == 404
    data = response.json()
    assert "error" in data  # Ensure an error message is returned

def test_query_batch_empty_name():
    # Querying with an empty query_name
    payload = {"query_name": ""}
    response = requests.post(f"{BASE_URL}/query", json=payload)
    # Expecting a 400 Bad Request response
    assert response.status_code == 400
    data = response.json()
    assert "error" in data  # Ensure an error message is returned

