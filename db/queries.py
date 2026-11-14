"""Database query helpers."""

from db.database import read_database, write_database


def insert_run(record):
    data = read_database()
    run = {
        "run_id": record.run_id,
        "timestamp": record.timestamp,
        "url": record.target_url,
        "pass_count": record.total_pass,
        "fail_count": record.total_fail,
    }
    data["runs"] = [item for item in data["runs"] if item["run_id"] != record.run_id]
    data["runs"].append(run)
    write_database(data)


def insert_test(run_id: str, result):
    data = read_database()
    item = result.model_dump()
    item["run_id"] = run_id
    data["tests"].append(item)
    write_database(data)


def insert_visual(run_id: str, log):
    data = read_database()
    data["visuals"].append(
        {
            "run_id": run_id,
            "test_name": getattr(log, "test_name", "visual check"),
            "status": log.status,
            "reason": log.reason,
        }
    )
    write_database(data)


def get_last_runs(n: int = 3):
    data = read_database()
    return sorted(data["runs"], key=lambda item: item["timestamp"], reverse=True)[:n]


def get_failures(run_id: str):
    data = read_database()
    return [
        item
        for item in data["tests"]
        if item["run_id"] == run_id and item["status"] in {"FAIL", "ERROR"}
    ]


def get_all_failures_by_test(test_name: str):
    data = read_database()
    return sum(
        1
        for item in data["tests"]
        if item["test_name"] == test_name and item["status"] in {"FAIL", "ERROR"}
    )
