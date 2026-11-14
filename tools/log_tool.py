"""Small terminal logger for live QA run progress."""

from datetime import datetime


def log_step(message: str) -> None:
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)
