"""Restore the latest non-expired EOD option snapshot in a GitHub Actions run.

This deliberately uses a short-retention Actions artifact rather than a cache:
cache eviction is nondeterministic and is not suitable for financial evidence.
"""

from __future__ import annotations

import io
import json
import os
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path


def request(url: str, token: str) -> bytes:
    response = urllib.request.urlopen(urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    ), timeout=20)
    return response.read()


def main() -> int:
    repository = os.getenv("GITHUB_REPOSITORY", "")
    token = os.getenv("GITHUB_TOKEN", "")
    if not repository or not token:
        print("No GitHub repository/token available; EOD OI comparison skipped.")
        return 0
    api_url = f"https://api.github.com/repos/{repository}/actions/artifacts?name=option-eod-snapshot&per_page=100"
    try:
        artifacts = json.loads(request(api_url, token)).get("artifacts", [])
        artifact = next((item for item in artifacts if not item.get("expired")), None)
        if artifact is None:
            print("No prior EOD option snapshot artifact found; comparison will start after today's EOD run.")
            return 0
        payload = request(artifact["archive_download_url"], token)
        root = Path.cwd().resolve()
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            with tempfile.TemporaryDirectory() as temporary:
                temporary_root = Path(temporary).resolve()
                for member in archive.infolist():
                    target = (temporary_root / member.filename).resolve()
                    if not target.is_relative_to(temporary_root):
                        raise ValueError("Artifact contains an unsafe path")
                archive.extractall(temporary_root)
                # upload-artifact may preserve either the `options` directory
                # or only its date children, depending on runner layout.
                source = next((path for path in temporary_root.rglob("options") if path.is_dir()), temporary_root)
                destination = root / "data" / "research" / "options"
                destination.mkdir(parents=True, exist_ok=True)
                for entry in source.iterdir():
                    target = destination / entry.name
                    if entry.is_dir():
                        shutil.copytree(entry, target, dirs_exist_ok=True)
                    elif entry.suffix == ".json":
                        shutil.copy2(entry, target)
        print(f"Restored EOD option snapshot created at {artifact.get('created_at', 'unknown time')}.")
        return 0
    except Exception as exc:
        print(f"Unable to restore EOD option snapshot; comparison skipped: {exc}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
