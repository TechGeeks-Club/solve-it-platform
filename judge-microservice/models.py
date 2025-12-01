"""
Pydantic models for Kafka message handling
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator


class SubmissionMessage(BaseModel):
    """Model for incoming submission messages from Kafka"""

    submission_id: int = Field(..., description="Unique submission identifier")
    task_id: int = Field(..., description="Task identifier")
    user_id: int = Field(..., description="User identifier")
    team_id: Optional[int] = Field(None, description="Team identifier (optional)")
    code: str = Field(..., min_length=1, description="Source code to evaluate")
    language_id: int = Field(50, description="Judge0 language ID (default: 50 for C)")

    class Config:
        json_schema_extra = {
            "example": {
                "submission_id": 123,
                "task_id": 5,
                "user_id": 42,
                "team_id": 7,
                "code": "#include <stdio.h>\nint main() { return 0; }",
                "language_id": 50,
            }
        }


class TestResult(BaseModel):
    """Model for individual test case result"""

    test_id: int
    passed: bool
    status: str
    execution_time: Optional[float] = None
    memory_usage: Optional[int] = None
    error_message: Optional[str] = None


class ExecutionResult(BaseModel):
    """Model for code execution results"""

    status: str = Field(..., description="Overall execution status")
    score: float = Field(0.0, ge=0.0, le=100.0, description="Score percentage (0-100)")
    passed_tests: int = Field(0, ge=0, description="Number of tests passed")
    total_tests: int = Field(0, ge=0, description="Total number of tests")
    test_results: Optional[List[TestResult]] = Field(
        None, description="Detailed test results"
    )
    error_message: Optional[str] = Field(
        None, description="Error message if execution failed"
    )

    @validator("passed_tests")
    def validate_passed_tests(cls, v, values):
        """Ensure passed_tests doesn't exceed total_tests"""
        if "total_tests" in values and v > values["total_tests"]:
            raise ValueError("passed_tests cannot exceed total_tests")
        return v


class ResultMessage(BaseModel):
    """Model for outgoing result messages to Kafka"""

    submission_id: int = Field(..., description="Unique submission identifier")
    task_id: int = Field(..., description="Task identifier")
    user_id: int = Field(..., description="User identifier")
    team_id: Optional[int] = Field(None, description="Team identifier (optional)")
    status: str = Field(..., description="Overall execution status")
    score: float = Field(0.0, ge=0.0, le=100.0, description="Score percentage (0-100)")
    passed_tests: int = Field(0, ge=0, description="Number of tests passed")
    total_tests: int = Field(0, ge=0, description="Total number of tests")
    test_results: Optional[List[TestResult]] = Field(
        None, description="Detailed test results"
    )
    error_message: Optional[str] = Field(
        None, description="Error message if execution failed"
    )
    processed_at: datetime = Field(
        default_factory=datetime.utcnow, description="Processing timestamp"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "submission_id": 123,
                "task_id": 5,
                "user_id": 42,
                "team_id": 7,
                "status": "completed",
                "score": 85.5,
                "passed_tests": 4,
                "total_tests": 5,
                "test_results": None,
                "error_message": None,
                "processed_at": "2025-11-28T12:00:00Z",
            }
        }

    def model_dump_json_compatible(self) -> dict:
        """Convert model to JSON-compatible dict"""
        return self.model_dump(mode="json")
