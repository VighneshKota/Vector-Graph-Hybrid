import urllib.request
import urllib.error
import json
import time

BASE_URL = "http://localhost:8000"  # Inside container, port is 8000

def print_step(msg):
    print(f"\n=== {msg} ===")

def make_request(method, endpoint, data=None):
    url = f"{BASE_URL}{endpoint}"
    headers = {'Content-Type': 'application/json'}
    
    if data:
        json_data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(url, data=json_data, headers=headers, method=method)
    else:
        req = urllib.request.Request(url, headers=headers, method=method)
        
    try:
        with urllib.request.urlopen(req) as response:
            status_code = response.getcode()
            response_body = response.read().decode('utf-8')
            try:
                json_response = json.loads(response_body)
            except:
                json_response = response_body
            return status_code, json_response
    except urllib.error.HTTPError as e:
        response_body = e.read().decode('utf-8')
        try:
            json_response = json.loads(response_body)
        except:
            json_response = response_body
        return e.code, json_response
    except Exception as e:
        print(f"Request failed: {e}")
        return 500, str(e)

def test_edge_crud():
    # 1. Create Nodes
    print_step("Creating Test Nodes")
    node1 = {
        "id": "test_node_1",
        "label": "TestNode",
        "properties": {"name": "Node1"}
    }
    node2 = {
        "id": "test_node_2",
        "label": "TestNode",
        "properties": {"name": "Node2"}
    }
    
    make_request("POST", "/nodes", node1)
    make_request("POST", "/nodes", node2)
    print("Nodes created (or already exist)")

    # 2. Create Edge
    print_step("Testing POST /edges")
    edge_data = {
        "source_id": "test_node_1",
        "target_id": "test_node_2",
        "type": "CONNECTS_TO",
        "weight": 1.0
    }
    
    status, response = make_request("POST", "/edges", edge_data)
    print(f"Status Code: {status}")
    print(f"Response: {response}")
    
    if status != 200:
        print("Failed to create edge")
        return

    edge_id = response.get("id")
    
    if not edge_id:
        print("FAIL: Edge ID not returned in response")
        return
    print(f"SUCCESS: Edge created with ID: {edge_id}")

    # 3. Update Edge
    print_step(f"Testing PUT /edges/{edge_id}")
    update_data = {
        "weight": 2.5
    }
    
    status, response = make_request("PUT", f"/edges/{edge_id}", update_data)
    print(f"Status Code: {status}")
    print(f"Response: {response}")
    
    if status == 200 and response.get("weight") == 2.5:
        print("SUCCESS: Edge updated successfully")
    else:
        print("FAIL: Edge update failed")

    # 4. Delete Edge
    print_step(f"Testing DELETE /edges/{edge_id}")
    status, response = make_request("DELETE", f"/edges/{edge_id}")
    print(f"Status Code: {status}")
    print(f"Response: {response}")
    
    if status == 200 and response.get("status") == "deleted":
        print("SUCCESS: Edge deleted successfully")
    else:
        print("FAIL: Edge deletion failed")

    # Cleanup Nodes
    print_step("Cleaning up Nodes")
    make_request("DELETE", "/nodes/test_node_1")
    make_request("DELETE", "/nodes/test_node_2")
    print("Cleanup complete")

if __name__ == "__main__":
    test_edge_crud()
