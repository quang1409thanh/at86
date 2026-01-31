from fastapi import APIRouter, HTTPException
from typing import List

from ...schemas import TestSummary, TestDetail, UserResult
from ...services import data_service

router = APIRouter(prefix="/toeic", tags=["toeic"])

@router.get("/tests", response_model=List[TestSummary])
def get_tests():
    return data_service.get_all_tests()

@router.get("/tests/{test_id}", response_model=TestDetail)
def get_test_detail(test_id: str):
    result = data_service.get_test_detail(test_id)
    if not result:
        raise HTTPException(status_code=404, detail="Test not found")
    return result

@router.post("/results")
def save_result(result: UserResult):
    data_service.save_result(result)
    return {"status": "success"}

@router.get("/results/{result_id}", response_model=UserResult)
def get_result(result_id: str):
    result = data_service.get_result_by_id(result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    return result

@router.delete("/tests/{test_id}")
def delete_test(test_id: str):
    success = data_service.delete_test(test_id)
    if not success:
        raise HTTPException(status_code=404, detail="Test not found or could not be deleted")
    return {"status": "success", "message": f"Test {test_id} deleted"}

@router.get("/history", response_model=List[UserResult])
def get_history():
    return data_service.get_history()
