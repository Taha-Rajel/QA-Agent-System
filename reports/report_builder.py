"""Build structured report data from test results."""

from collections import defaultdict
from datetime import datetime
from uuid import uuid4

from config import TARGET_URL as DEFAULT_TARGET_URL
from db.queries import insert_run, insert_test
from models import RunRecord


def build_report_data(results, target_url: str | None = None):
    """Compute report totals and grouping for HTML rendering."""
    target_url = target_url or DEFAULT_TARGET_URL
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    run_id = uuid4().hex
    total_pass = sum(1 for result in results if result.status == "PASS")
    total_fail = sum(1 for result in results if result.status in {"FAIL", "ERROR"})
    total_info = sum(1 for result in results if result.status == "INFO")
    grouped = defaultdict(list)

    for item in results:
        grouped[item.agent].append(item)

    record = RunRecord(
        run_id=run_id,
        timestamp=timestamp,
        target_url=target_url,
        total_pass=total_pass,
        total_fail=total_fail,
        results=results,
    )
    insert_run(record)
    for item in results:
        insert_test(run_id, item)

    return {
        "run_id": run_id,
        "timestamp": timestamp,
        "target_url": target_url,
        "results": results,
        "grouped_results": dict(grouped),
        "total_pass": total_pass,
        "total_fail": total_fail,
        "total_info": total_info,
        "total_tests": len(results),
        "total_duration_ms": sum(result.duration_ms for result in results),
    }
