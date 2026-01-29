import os
import json
from typing import List
from datetime import datetime
from schemas import TestSummary, TestDetail, UserResult

DATA_DIR = "../data/tests"
USER_DATA_DIR = "../data/users/default" # Single user for now

if not os.path.exists(USER_DATA_DIR):
    os.makedirs(USER_DATA_DIR)

def get_all_tests() -> List[TestSummary]:
    tests = []
    if not os.path.exists(DATA_DIR):
        return []
    
    for folder_name in os.listdir(DATA_DIR):
        folder_path = os.path.join(DATA_DIR, folder_name)
        file_path = os.path.join(folder_path, "test.json")
        if os.path.isdir(folder_path) and os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    tests.append(TestSummary(
                        test_id=data.get("test_id", folder_name),
                        title=data.get("title", folder_name),
                        path=folder_name
                    ))
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
    return tests

def get_test_detail(test_folder: str) -> TestDetail:
    file_path = os.path.join(DATA_DIR, test_folder, "test.json")
    if not os.path.exists(file_path):
        return None
    
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return TestDetail(**data)

def save_result(result: UserResult):
    file_name = f"{result.id}.json"
    file_path = os.path.join(USER_DATA_DIR, file_name)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(result.json())
    return True

def get_result_by_id(result_id: str) -> UserResult:
    file_path = os.path.join(USER_DATA_DIR, f"{result_id}.json")
    if not os.path.exists(file_path):
        return None
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return UserResult(**data)

def get_history() -> List[UserResult]:
    results = []
    if not os.path.exists(USER_DATA_DIR):
        return []
        
    for file_name in os.listdir(USER_DATA_DIR):
        if file_name.endswith(".json"):
            try:
                with open(os.path.join(USER_DATA_DIR, file_name), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    results.append(UserResult(**data))
            except Exception as e:
                print(f"Error loading result {file_name}: {e}")
    
    # Sort by timestamp desc
    results.sort(key=lambda x: x.timestamp, reverse=True)
    return results
