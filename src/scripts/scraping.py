"""Download the Agenda Tech database JSON into the local db folder."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Final
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_SOURCE_URL: Final[str] = (
	"https://raw.githubusercontent.com/agenda-tech-brasil/agenda-tech-brasil/main/src/db/database.json"
)
DEFAULT_OUTPUT_PATH: Final[Path] = Path(__file__).resolve().parents[1] / "db" / "database.json"


def fetch_remote_json(url: str) -> str:
	"""Return the remote JSON payload as a string, raising for HTTP issues."""

	request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
	try:
		with urlopen(request, timeout=30) as response:  # nosec: B310 - remote host is trusted
			charset = response.headers.get_content_charset() or "utf-8"
			payload = response.read().decode(charset)
	except HTTPError as exc:  # pragma: no cover - network failure cases
		raise RuntimeError(f"failed to download database (HTTP {exc.code})") from exc
	except URLError as exc:  # pragma: no cover - network failure cases
		raise RuntimeError("failed to reach database host") from exc

	# Validate JSON before writing to disk to avoid corrupting local history.
	json.loads(payload)
	return payload


def persist_database(raw_json: str, output_path: Path) -> None:
	"""Write a formatted JSON payload to disk, creating the parent directory if needed."""

	output_path.parent.mkdir(parents=True, exist_ok=True)
	parsed = json.loads(raw_json)
	formatted = json.dumps(parsed, indent=2, ensure_ascii=False, sort_keys=False)
	output_path.write_text(f"{formatted}\n", encoding="utf-8")


def download_database(url: str, destination: Path) -> None:
	"""High level helper that downloads the remote JSON and persists it locally."""

	raw_payload = fetch_remote_json(url)
	persist_database(raw_payload, destination)


def parse_args(argv: list[str]) -> argparse.Namespace:
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("--url", default=DEFAULT_SOURCE_URL, help="Remote JSON endpoint")
	parser.add_argument(
		"--output",
		default=str(DEFAULT_OUTPUT_PATH),
		help="Destination path for the downloaded database",
	)
	return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
	args = parse_args(sys.argv[1:] if argv is None else argv)
	destination = Path(args.output).expanduser().resolve()

	try:
		download_database(args.url, destination)
	except RuntimeError as exc:
		print(exc, file=sys.stderr)
		return 1

	print(f"Database stored at {destination}")
	return 0


if __name__ == "__main__":  # pragma: no cover - script entry point
	raise SystemExit(main())
