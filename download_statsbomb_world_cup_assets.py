#!/usr/bin/env python3
"""Download StatsBomb event and lineup files for 2018/2022 World Cup matches."""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path


BASE_DIR = Path("/Users/evelynfeng/Documents/gaming")
MATCH_DIR = BASE_DIR / "data" / "statsbomb" / "matches"
EVENT_DIR = BASE_DIR / "data" / "statsbomb" / "events"
LINEUP_DIR = BASE_DIR / "data" / "statsbomb" / "lineups"

MATCH_FILES = [
    MATCH_DIR / "world_cup_2018_matches.json",
    MATCH_DIR / "world_cup_2022_matches.json",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--asset",
        choices=["events", "lineups", "both"],
        default="both",
        help="Which StatsBomb asset type to download.",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.05,
        help="Delay between requests in seconds.",
    )
    return parser.parse_args()


def load_match_ids() -> list[int]:
    match_ids: list[int] = []
    for path in MATCH_FILES:
        rows = json.loads(path.read_text())
        match_ids.extend(int(row["match_id"]) for row in rows)
    return match_ids


def is_valid_json_file(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        json.loads(path.read_text())
    except Exception:
        return False
    return True


def download_file(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    if temporary.exists():
        temporary.unlink()
    with urllib.request.urlopen(url, timeout=60) as response:
        temporary.write_bytes(response.read())
    json.loads(temporary.read_text())
    temporary.replace(destination)


def download_assets(match_ids: list[int], asset: str, out_dir: Path, pause: float) -> None:
    total = len(match_ids)
    for index, match_id in enumerate(match_ids, start=1):
        destination = out_dir / f"{match_id}.json"
        if is_valid_json_file(destination):
            print(f"[skip] {asset} {match_id} already exists")
            continue
        if destination.exists():
            print(f"[redo] {asset} {match_id} invalid or partial file found")

        url = f"https://raw.githubusercontent.com/statsbomb/open-data/master/data/{asset}/{match_id}.json"
        try:
            download_file(url, destination)
            print(f"[ok]   {asset} {match_id} ({index}/{total})")
        except urllib.error.HTTPError as exc:
            print(f"[fail] {asset} {match_id} HTTP {exc.code}")
        except urllib.error.URLError as exc:
            print(f"[fail] {asset} {match_id} URL error: {exc.reason}")
            raise
        time.sleep(pause)


def main() -> None:
    args = parse_args()
    match_ids = load_match_ids()

    if args.asset in {"events", "both"}:
        download_assets(match_ids, "events", EVENT_DIR, args.sleep)

    if args.asset in {"lineups", "both"}:
        download_assets(match_ids, "lineups", LINEUP_DIR, args.sleep)


if __name__ == "__main__":
    main()
