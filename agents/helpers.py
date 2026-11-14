"""Small shared helpers for agents."""

from time import perf_counter

from models import TestResult
from tools.log_tool import log_step


def result(agent: str, test_name: str, status: str, detail: str, started: float, screenshot_path: str | None = None) -> TestResult:
    duration_ms = int((perf_counter() - started) * 1000)
    log_step(f"{agent}: {test_name} -> {status} ({duration_ms}ms)")
    return TestResult(
        agent=agent,
        test_name=test_name,
        status=status,
        screenshot_path=screenshot_path,
        detail=detail,
        duration_ms=duration_ms,
    )


def fail(agent: str, test_name: str, exc: Exception, started: float) -> TestResult:
    return result(agent, test_name, "ERROR", str(exc), started)
