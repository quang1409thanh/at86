import os
import json
import random
from datetime import datetime
import sys

# Setup paths - assuming running from project root
sys.path.append(os.getcwd())

# Manually defining paths to match backend config
DATA_DIR = os.path.abspath("data")
USER_DATA_DIR = os.path.join(DATA_DIR, "users", "default")
TESTS_DIR = os.path.join(DATA_DIR, "tests")

if not os.path.exists(USER_DATA_DIR):
    os.makedirs(USER_DATA_DIR)

# Get available test IDs
available_tests = []
if os.path.exists(TESTS_DIR):
    for folder in os.listdir(TESTS_DIR):
        if os.path.isdir(os.path.join(TESTS_DIR, folder)):
            available_tests.append(folder)

print(f"Found tests: {available_tests}")

if not available_tests:
    print("No tests found to generate history for. Ensure data/tests has content.")
    # Create a dummy test if none exists for demo
    dummy_id = "TOEIC_DEMO_01"
    os.makedirs(os.path.join(TESTS_DIR, dummy_id), exist_ok=True)
    with open(os.path.join(TESTS_DIR, dummy_id, "test.json"), "w") as f:
        json.dump({"test_id": dummy_id, "title": "Demo Test 01"}, f)
    available_tests.append(dummy_id)

# Generate 5-10 random results
num_results = 8

for i in range(num_results):
    test_id = random.choice(available_tests)
    score = random.randint(300, 950) # TOEIC score range roughly
    
    answers = {} 
    
    result_id = f"res_{int(datetime.now().timestamp())}_{i}"
    
    result_data = {
        "id": result_id,
        "test_id": test_id,
        "timestamp": datetime.now().isoformat(),
        "score": score,
        "total_questions": 200,
        "correct_count": int(score / 5), # A rough approximation
        "answers": answers
    }
    
    file_path = os.path.join(USER_DATA_DIR, f"{result_id}.json")
    with open(file_path, "w") as f:
        json.dump(result_data, f, indent=2)
    
    print(f"Generated result {result_id} for {test_id}: Score {score}")

print("Seeding complete.")
