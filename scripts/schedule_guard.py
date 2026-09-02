"""Prevent fallback cron entries from sending the same brief twice."""

from __future__ import annotations

from datetime import datetime
import os
from pathlib import PurePosixPath
from zoneinfo import ZoneInfo

import requests


def _write(skip: bool, reason: str) -> None:
    print(reason)
    output = os.getenv("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as handle:
            handle.write(f"skip={'true' if skip else 'false'}\n")


def main() -> None:
    if os.getenv("GITHUB_EVENT_NAME") != "schedule":
        _write(False, "Manual dispatch: idempotency guard disabled")
        return
    token = os.getenv("GITHUB_TOKEN")
    repository = os.getenv("GITHUB_REPOSITORY")
    workflow_ref = os.getenv("GITHUB_WORKFLOW_REF", "")
    current_run = int(os.getenv("GITHUB_RUN_ID", "0"))
    if not token or not repository or not workflow_ref:
        _write(False, "Guard context incomplete; proceeding so a scheduled brief is not lost")
        return
    workflow_file = PurePosixPath(workflow_ref.split("@", 1)[0]).name
    url = f"https://api.github.com/repos/{repository}/actions/workflows/{workflow_file}/runs"
    response = requests.get(
        url,
        params={"event": "schedule", "status": "success", "per_page": 30},
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        timeout=15,
    )
    response.raise_for_status()
    today_ist = datetime.now(ZoneInfo("Asia/Kolkata")).date()
    for run in response.json().get("workflow_runs", []):
        if int(run.get("id") or 0) == current_run:
            continue
        started = run.get("run_started_at") or run.get("created_at")
        if not started:
            continue
        observed = datetime.fromisoformat(started.replace("Z", "+00:00")).astimezone(ZoneInfo("Asia/Kolkata"))
        if observed.date() == today_ist:
            _write(True, f"A successful scheduled run already sent this panel today: {run.get('html_url')}")
            return
    _write(False, "No successful scheduled run found for today; send this panel")


if __name__ == "__main__":
    main()
