import os
import json

def update_test_json(test_id, part_number, questions, output_dir, title=None, instructions=None):
    """
    Updates the final test.json and an intermediate backup file immediately.
    Ensures that data is persisted even if the process is interrupted.
    """
    test_json_path = os.path.join(output_dir, "test.json")
    backup_json_path = os.path.join("tools/pipeline", f"part{part_number}_final.json")
    
    # Ensure directories exist
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs("tools/pipeline", exist_ok=True)

    data = {
        "test_id": test_id,
        "title": title or f"TOEIC Part {part_number} - Practice",
        "parts": []
    }

    # 1. Load existing data if available to keep other parts intact
    if os.path.exists(test_json_path):
        try:
            with open(test_json_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                data["test_id"] = existing_data.get("test_id", data["test_id"])
                data["title"] = existing_data.get("title", data["title"])
                data["parts"] = existing_data.get("parts", [])
        except Exception as e:
            print(f"[!] Warning: Could not read existing test.json: {e}")

    # 2. Update or add the target part
    part_found = False
    for part in data["parts"]:
        if part.get("part_number") == part_number:
            part["questions"] = questions
            if instructions:
                part["instructions"] = instructions
            part_found = True
            break
    
    if not part_found:
        data["parts"].append({
            "part_number": part_number,
            "instructions": instructions or "",
            "questions": questions
        })

    # Sort parts by part_number
    data["parts"].sort(key=lambda x: x.get("part_number", 0))

    # 3. Save to deployment location
    with open(test_json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        
    # Legacy backup removed to prevent conflict with multi-test merging

    return data

def load_progress(part_number, file_path=None):
    """
    Loads existing progress for a specific part.
    If file_path (test.json) is provided, it tries to load from there first.
    Falls back to the intermediate backup if provided or legacy path.
    """
    paths_to_check = []
    if file_path:
        paths_to_check.append(file_path)
    
    # Also check legacy backup just in case
    # backup_json_path = os.path.join("tools/pipeline", f"part{part_number}_final.json")
    # paths_to_check.append(backup_json_path)

    for path in paths_to_check:
        if path and os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for part in data.get("parts", []):
                        if part.get("part_number") == part_number:
                            questions = part.get("questions", [])
                            if questions:
                                return questions
            except Exception as e:
                print(f"[!] Warn: Failed to load progress from {path}: {e}")
                pass
    return []
