"""Shared data models used across agents, storage, and reports."""

from pydantic import BaseModel


class TestResult(BaseModel):
    agent: str
    test_name: str
    status: str
    screenshot_path: str | None = None
    detail: str = ""
    duration_ms: int = 0


class VisualLog(BaseModel):
    status: str
    reason: str
    embedding_id: str | None = None


class RunRecord(BaseModel):
    run_id: str
    timestamp: str
    target_url: str
    total_pass: int
    total_fail: int
    results: list[TestResult]
