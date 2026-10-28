import requests
import pandas as pd
import io

BASE_URL = "http://localhost:8007"

def create_sample_csv():
    # Includes dirty data ('$15') to test robustness
    data = """id,2023-01,2023-02,2023-03
A,10,$15,20
B,20,25,30
C,30,35,40"""
    return data

def test_visualization():
    print("1. Creating sample data...")
    csv_content = create_sample_csv()
    files = {'file': ('test.csv', csv_content, 'text/csv')}
    
    print("2. Uploading file...")
    response = requests.post(f"{BASE_URL}/upload", files=files)
    if response.status_code != 200:
        print(f"Upload failed: {response.text}")
        return
    
    dataset_id = response.json()['dataset_id']
    print(f"Dataset ID: {dataset_id}")
    
    print("3. Testing visualization on RAW data (Bar Chart)...")
    # 2023-02 contains '$15' so it is an object column. 
    # If backend logic is strict, this will NOT be in the numeric list, and frontend would block it.
    # We want to verify if we CAN visualize it if we force the request (backend fix) 
    # AND if checking viz types (frontend fix preparation) sees it.
    
    viz_types_response = requests.get(f"{BASE_URL}/dataset/{dataset_id}/visualization/types")
    viz_types = viz_types_response.json()
    numeric_cols = viz_types['current_columns']['numeric']
    print(f"DEBUG: Raw data numeric columns: {numeric_cols}")
    if "2023-02" not in numeric_cols:
         print("⚠ CRITICAL: Dirty column '2023-02' is NOT detected as numeric.")

    viz_payload = {
        "chart_type": "bar_chart",
        "parameters": {
            "x_column": "id",
            "y_columns": ["2023-02"], # Dirty column
            "title": "Raw Data Dirty Column Chart"
        }
    }
    response = requests.post(f"{BASE_URL}/dataset/{dataset_id}/visualize", json=viz_payload)
    if response.status_code == 200:
        print("✓ Raw data (dirty column) visualization successful")
    else:
        print(f"✗ Raw data (dirty column) visualization failed: {response.text}")

    print("4. Performing MELT operation...")
    melt_payload = {
        "id_cols": ["id"],
        "period_cols": ["2023-01", "2023-02", "2023-03"],
        "value_name": "Value",
        "var_name": "Period",
        "auto_detect": False
    }
    response = requests.post(f"{BASE_URL}/dataset/{dataset_id}/melt", json=melt_payload)
    if response.status_code != 200:
        print(f"Melt failed: {response.text}")
        return
    print("✓ Melt successful")

    print("5. Testing visualization on TRANSFORMED data (Bar Chart)...")
    
    # NEW STEP: Check if backend sees the columns as numeric
    viz_types_response = requests.get(f"{BASE_URL}/dataset/{dataset_id}/visualization/types")
    if viz_types_response.status_code == 200:
        viz_types = viz_types_response.json()
        numeric_cols = viz_types['current_columns']['numeric']
        print(f"DEBUG: Numeric columns detected by backend: {numeric_cols}")
        if "Value" not in numeric_cols:
            print("⚠ CRITICAL: 'Value' column is NOT detected as numeric! This is likely why the frontend fails.")
    
    # After melt, we have 'id', 'Period', 'Value'
    viz_payload = {
        "chart_type": "bar_chart",
        "parameters": {
            "x_column": "Period",
            "y_columns": ["Value"],
            "group_column": "id",
            "title": "Transformed Data Chart"
        }
    }
    response = requests.post(f"{BASE_URL}/dataset/{dataset_id}/visualize", json=viz_payload)
    if response.status_code == 200:
        print("✓ Transformed data visualization successful")
    else:
        print(f"✗ Transformed data visualization failed: {response.text}")

if __name__ == "__main__":
    try:
        test_visualization()
    except Exception as e:
        print(f"An error occurred: {e}")
