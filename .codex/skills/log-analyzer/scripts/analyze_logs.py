#!/usr/bin/env python3

from __future__ import annotations

import argparse
import bz2
import gzip
import io
import json
import lzma
import re
import sys
import tarfile
import zipfile
from collections import Counter, defaultdict
from pathlib import Path


TEXT_FILE_HINTS = (
    ".log",
    ".txt",
    ".out",
    ".err",
    ".trace",
    ".json",
    ".ndjson",
)
MULTI_FILE_ARCHIVES = (
    ".zip",
    ".tar",
    ".tar.gz",
    ".tgz",
    ".tar.bz2",
    ".tbz2",
    ".tar.xz",
    ".txz",
)
SINGLE_FILE_COMPRESSED = (
    ".gz",
    ".bz2",
    ".xz",
)
UNSUPPORTED_ARCHIVES = (
    ".rar",
    ".7z",
)
LEVEL_ALIASES = {
    "WARNING": "WARN",
    "SEVERE": "ERROR",
    "CRITICAL": "FATAL",
}
EVENT_START_PATTERNS = (
    re.compile(r"^\[?\d{4}[-/]\d{2}[-/]\d{2}[ T]"),
    re.compile(r"^\d{2}:\d{2}:\d{2}(?:[.,]\d+)?\b"),
    re.compile(r"^[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\b"),
    re.compile(r"^Traceback \(most recent call last\):"),
    re.compile(r"^\[?(TRACE|DEBUG|INFO|WARN|WARNING|ERROR|FATAL|SEVERE|CRITICAL)\]?[\s:]"),
    re.compile(r"^(?:time=|ts=)?[^ ]*\s*(?:level|lvl)=(trace|debug|info|warn|warning|error|fatal)\b", re.IGNORECASE),
)
STACK_CONTINUATION_PATTERNS = (
    re.compile(r"^\s+at\s"),
    re.compile(r"^\s*Caused by:"),
    re.compile(r"^\s*Suppressed:"),
    re.compile(r"^\s*\.\.\. \d+ more"),
    re.compile(r'^\s*File "'),
    re.compile(r"^\s*During handling of the above exception"),
)
HEADER_PATTERNS = (
    re.compile(
        r"^(?P<timestamp>\[?\d{4}[-/]\d{2}[-/]\d{2}[^\]]*\]?)"
        r"(?:\s+|,\s*)"
        r"(?P<level>TRACE|DEBUG|INFO|WARN(?:ING)?|ERROR|FATAL|SEVERE|CRITICAL)\b"
        r"(?:\s+\[[^\]]+\])?"
        r"(?:\s+(?P<logger>[A-Za-z0-9_.$/-]+))?"
        r"\s*(?:-|:)\s*(?P<message>.*)$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\[(?P<level>TRACE|DEBUG|INFO|WARN(?:ING)?|ERROR|FATAL|SEVERE|CRITICAL)\]"
        r"(?:\s+(?P<logger>[A-Za-z0-9_.$/-]+))?"
        r"\s*(?:-|:)\s*(?P<message>.*)$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^(?P<level>TRACE|DEBUG|INFO|WARN(?:ING)?|ERROR|FATAL|SEVERE|CRITICAL)\b"
        r"(?:\s+(?P<logger>[A-Za-z0-9_.$/-]+))?"
        r"\s*(?:-|:)\s*(?P<message>.*)$",
        re.IGNORECASE,
    ),
)
JSON_MESSAGE_KEYS = ("message", "msg", "event", "error")
JSON_LEVEL_KEYS = ("level", "severity", "lvl")
JSON_LOGGER_KEYS = ("logger", "name", "component")
GENERAL_EXCEPTION_RE = re.compile(
    r"(?:(?:Caused by|Suppressed):\s*)?"
    r"(?P<type>(?:[\w$]+\.)*[\w$]*(?:Exception|Error|Throwable))"
    r"(?::\s*(?P<message>.*))?$"
)
PYTHON_EXCEPTION_RE = re.compile(
    r"^(?P<type>(?:[\w.]+)?(?:Exception|Error))(?::\s*(?P<message>.*))?$"
)
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
UUID_RE = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.IGNORECASE)
URL_RE = re.compile(r"https?://\S+")
IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
HEX_RE = re.compile(r"\b(?:0x)?[0-9a-f]{8,}\b", re.IGNORECASE)
NUMBER_RE = re.compile(r"\b\d+\b")
TIMESTAMP_RE = re.compile(
    r"\b\d{4}[-/]\d{2}[-/]\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})?\b"
)
UNIX_PATH_RE = re.compile(r"(?<!<)(?:/[^\s:]+)+")
WINDOWS_PATH_RE = re.compile(r"\b[A-Za-z]:\\[^\s:]+")
QUOTED_RE = re.compile(r"\"[^\"]*\"|'[^']*'")
MAX_STACK_PREVIEW_LINES = 12


def canonicalize_level(level: str | None) -> str | None:
    if not level:
        return None
    normalized = level.strip().upper()
    return LEVEL_ALIASES.get(normalized, normalized)


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def sort_counter(counter: Counter, limit: int) -> list[tuple[str, int]]:
    return sorted(counter.items(), key=lambda item: (-item[1], item[0]))[:limit]


def counter_to_rows(counter: Counter, key_name: str, limit: int) -> list[dict[str, object]]:
    return [{key_name: key, "count": count} for key, count in sort_counter(counter, limit)]


def nested_counter_to_rows(counter: Counter, key_name: str, limit: int) -> list[dict[str, object]]:
    return [{key_name: key, "count": count} for key, count in sort_counter(counter, limit)]


def looks_like_log_candidate(name: str) -> bool:
    lowered = name.lower()
    base_name = Path(lowered).name
    if any(lowered.endswith(suffix) for suffix in TEXT_FILE_HINTS + MULTI_FILE_ARCHIVES + SINGLE_FILE_COMPRESSED):
        return True
    if base_name in {"stdout", "stderr", "syslog", "messages"}:
        return True
    return "log" in base_name or "trace" in base_name


def is_probable_event_start(line: str) -> bool:
    stripped = strip_ansi(line.rstrip("\n"))
    if not stripped:
        return False
    if stripped.startswith("{") and any(key in stripped for key in ('"level"', '"message"', '"msg"', '"severity"')):
        return True
    return any(pattern.match(stripped) for pattern in EVENT_START_PATTERNS)


def is_stack_continuation(line: str) -> bool:
    stripped = strip_ansi(line.rstrip("\n"))
    if not stripped:
        return True
    if stripped.startswith("    ") or stripped.startswith("\t"):
        return True
    return any(pattern.match(stripped) for pattern in STACK_CONTINUATION_PATTERNS)


def normalize_message(message: str) -> str:
    text = strip_ansi(message).strip()
    text = TIMESTAMP_RE.sub("<time>", text)
    text = UUID_RE.sub("<uuid>", text)
    text = URL_RE.sub("<url>", text)
    text = IPV4_RE.sub("<ip>", text)
    text = WINDOWS_PATH_RE.sub("<path>", text)
    text = UNIX_PATH_RE.sub("<path>", text)
    text = HEX_RE.sub("<hex>", text)
    text = QUOTED_RE.sub("<str>", text)
    text = NUMBER_RE.sub("<num>", text)
    text = re.sub(r"\s+", " ", text)
    text = text.strip(" -:")
    return text or "<empty>"


def maybe_parse_json_line(line: str) -> dict[str, str | None] | None:
    stripped = line.strip()
    if not (stripped.startswith("{") and stripped.endswith("}")):
        return None
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None

    message = None
    for key in JSON_MESSAGE_KEYS:
        if payload.get(key) not in (None, ""):
            message = str(payload[key])
            break

    level = None
    for key in JSON_LEVEL_KEYS:
        if payload.get(key) not in (None, ""):
            level = canonicalize_level(str(payload[key]))
            break

    logger = None
    for key in JSON_LOGGER_KEYS:
        if payload.get(key) not in (None, ""):
            logger = str(payload[key])
            break

    if not message and not level and not logger:
        return None
    return {"level": level, "logger": logger, "message": message or stripped}


def maybe_parse_logfmt_line(line: str) -> dict[str, str | None] | None:
    if "level=" not in line and "lvl=" not in line:
        return None
    pairs = dict(re.findall(r'([A-Za-z0-9_.-]+)=(".*?"|\'.*?\'|\S+)', line))
    if not pairs:
        return None
    level = canonicalize_level(strip_quotes(pairs.get("level") or pairs.get("lvl")))
    logger = strip_quotes(pairs.get("logger") or pairs.get("component") or pairs.get("name"))
    message = strip_quotes(
        pairs.get("msg") or pairs.get("message") or pairs.get("event") or pairs.get("error")
    )
    if not level and not logger and not message:
        return None
    return {"level": level, "logger": logger, "message": message or line.strip()}


def strip_quotes(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def parse_header(first_line: str) -> dict[str, str | None]:
    stripped = strip_ansi(first_line.strip())

    parsed = maybe_parse_json_line(stripped)
    if parsed:
        return parsed

    parsed = maybe_parse_logfmt_line(stripped)
    if parsed:
        return parsed

    for pattern in HEADER_PATTERNS:
        match = pattern.match(stripped)
        if match:
            return {
                "level": canonicalize_level(match.groupdict().get("level")),
                "logger": match.groupdict().get("logger"),
                "message": (match.groupdict().get("message") or stripped).strip(),
            }

    return {"level": None, "logger": None, "message": stripped}


def extract_exception(lines: list[str]) -> dict[str, object] | None:
    cleaned_lines = [strip_ansi(line.rstrip("\n")) for line in lines if line.strip()]
    if not cleaned_lines:
        return None

    if any(line.startswith("Traceback (most recent call last):") for line in cleaned_lines):
        for candidate in reversed(cleaned_lines):
            match = PYTHON_EXCEPTION_RE.match(candidate.strip())
            if match:
                exc_type = match.group("type").split(".")[-1]
                message = (match.group("message") or "").strip()
                return {
                    "type": exc_type,
                    "message": message,
                    "key": exc_type if not message else f"{exc_type}: {normalize_message(message)}",
                    "stack_preview": cleaned_lines[:MAX_STACK_PREVIEW_LINES],
                }

    for candidate in cleaned_lines:
        match = GENERAL_EXCEPTION_RE.search(candidate.strip())
        if match:
            exc_type = match.group("type").split(".")[-1]
            message = (match.group("message") or "").strip()
            return {
                "type": exc_type,
                "message": message,
                "key": exc_type if not message else f"{exc_type}: {normalize_message(message)}",
                "stack_preview": cleaned_lines[:MAX_STACK_PREVIEW_LINES],
            }

    return None


def is_binary_sample(sample: bytes) -> bool:
    if not sample:
        return False
    if b"\x00" in sample:
        return True
    textish = sum(byte in b"\t\n\r\f\b" or 32 <= byte <= 126 for byte in sample)
    return textish / max(len(sample), 1) < 0.7


class Analyzer:
    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.total_lines = 0
        self.total_events = 0
        self.files_scanned = 0
        self.archive_members_scanned = 0
        self.message_counts: Counter[str] = Counter()
        self.message_levels: defaultdict[str, Counter[str]] = defaultdict(Counter)
        self.message_loggers: defaultdict[str, Counter[str]] = defaultdict(Counter)
        self.message_sources: defaultdict[str, Counter[str]] = defaultdict(Counter)
        self.message_samples: dict[str, dict[str, str | None]] = {}
        self.level_counts: Counter[str] = Counter()
        self.exception_type_counts: Counter[str] = Counter()
        self.exception_counts: Counter[str] = Counter()
        self.exception_sources: defaultdict[str, Counter[str]] = defaultdict(Counter)
        self.exception_levels: defaultdict[str, Counter[str]] = defaultdict(Counter)
        self.exception_samples: dict[str, dict[str, object]] = {}
        self.source_event_counts: Counter[str] = Counter()
        self.source_exception_counts: Counter[str] = Counter()
        self.skipped_inputs: list[dict[str, str]] = []

    def add_skip(self, source: str, reason: str) -> None:
        self.skipped_inputs.append({"source": source, "reason": reason})

    def register_source(self, from_archive: bool) -> None:
        if from_archive:
            self.archive_members_scanned += 1
        else:
            self.files_scanned += 1

    def consume_event(self, source: str, event_lines: list[str]) -> None:
        if not event_lines:
            return
        full_text = "\n".join(line.rstrip("\n") for line in event_lines).strip()
        if not full_text:
            return

        self.total_events += 1
        self.source_event_counts[source] += 1

        header = parse_header(event_lines[0])
        level = header.get("level")
        logger = header.get("logger")
        message = (header.get("message") or strip_ansi(event_lines[0].strip()) or "<empty>").strip()
        exception = extract_exception(event_lines)
        if exception and (message.startswith("Traceback (most recent call last)") or message == "<empty>"):
            exception_message = str(exception["message"]).strip()
            message = str(exception["type"]) if not exception_message else f"{exception['type']}: {exception_message}"
        message_key = normalize_message(message)

        self.message_counts[message_key] += 1
        self.message_sources[message_key][source] += 1
        if level:
            self.level_counts[level] += 1
            self.message_levels[message_key][level] += 1
        if logger:
            self.message_loggers[message_key][logger] += 1
        if message_key not in self.message_samples:
            self.message_samples[message_key] = {
                "sample_message": message,
                "sample_level": level,
                "sample_logger": logger,
                "sample_source": source,
            }

        if not exception:
            return

        exc_type = str(exception["type"])
        exc_key = str(exception["key"])
        self.exception_type_counts[exc_type] += 1
        self.exception_counts[exc_key] += 1
        self.exception_sources[exc_key][source] += 1
        self.source_exception_counts[source] += 1
        if level:
            self.exception_levels[exc_key][level] += 1
        if exc_key not in self.exception_samples:
            self.exception_samples[exc_key] = {
                "type": exc_type,
                "sample_message": exception["message"],
                "sample_source": source,
                "stack_preview": exception["stack_preview"],
            }

    def process_text_stream(self, source: str, binary_stream: io.BufferedIOBase, from_archive: bool) -> None:
        buffered = io.BufferedReader(binary_stream)
        sample = buffered.peek(2048)[:2048]
        if not sample:
            self.add_skip(source, "empty file")
            return
        if is_binary_sample(sample):
            self.add_skip(source, "binary or unsupported content")
            return

        self.register_source(from_archive)
        current_event: list[str] = []
        text_stream = io.TextIOWrapper(buffered, encoding="utf-8", errors="replace")
        try:
            for line in text_stream:
                self.total_lines += 1
                if not current_event:
                    current_event.append(line)
                    continue

                if is_probable_event_start(line) and not is_stack_continuation(line):
                    self.consume_event(source, current_event)
                    current_event = [line]
                else:
                    current_event.append(line)
        finally:
            try:
                text_stream.detach()
            except Exception:
                pass

        self.consume_event(source, current_event)

    def build_report(self, input_path: Path) -> dict[str, object]:
        top_messages = []
        for key, count in sort_counter(self.message_counts, self.limit):
            sample = self.message_samples[key]
            top_messages.append(
                {
                    "pattern": key,
                    "count": count,
                    "sample_message": sample["sample_message"],
                    "sample_level": sample["sample_level"],
                    "sample_logger": sample["sample_logger"],
                    "sample_source": sample["sample_source"],
                    "levels": nested_counter_to_rows(self.message_levels[key], "level", 5),
                    "loggers": nested_counter_to_rows(self.message_loggers[key], "logger", 5),
                    "sources": nested_counter_to_rows(self.message_sources[key], "source", 5),
                }
            )

        exceptions = []
        for key, count in sort_counter(self.exception_counts, self.limit):
            sample = self.exception_samples[key]
            exceptions.append(
                {
                    "key": key,
                    "type": sample["type"],
                    "count": count,
                    "sample_message": sample["sample_message"],
                    "sample_source": sample["sample_source"],
                    "levels": nested_counter_to_rows(self.exception_levels[key], "level", 5),
                    "sources": nested_counter_to_rows(self.exception_sources[key], "source", 5),
                    "stack_preview": sample["stack_preview"],
                }
            )

        noisiest_sources = []
        for source, count in sort_counter(self.source_event_counts, self.limit):
            noisiest_sources.append(
                {
                    "source": source,
                    "events": count,
                    "exception_events": self.source_exception_counts[source],
                }
            )

        return {
            "input_path": str(input_path),
            "summary": {
                "files_scanned": self.files_scanned,
                "archive_members_scanned": self.archive_members_scanned,
                "sources_scanned": self.files_scanned + self.archive_members_scanned,
                "total_lines": self.total_lines,
                "total_events": self.total_events,
            },
            "levels": counter_to_rows(self.level_counts, "level", 10),
            "top_messages": top_messages,
            "exception_types": counter_to_rows(self.exception_type_counts, "type", self.limit),
            "exceptions": exceptions,
            "noisiest_sources": noisiest_sources,
            "skipped_inputs": self.skipped_inputs,
        }


def scan_plain_file(path: Path, analyzer: Analyzer) -> None:
    try:
        with path.open("rb") as handle:
            analyzer.process_text_stream(str(path), handle, from_archive=False)
    except OSError as exc:
        analyzer.add_skip(str(path), f"read failure: {exc}")


def scan_single_file_archive(path: Path, analyzer: Analyzer) -> None:
    opener = None
    lowered = path.name.lower()
    if lowered.endswith(".gz"):
        opener = gzip.open
    elif lowered.endswith(".bz2"):
        opener = bz2.open
    elif lowered.endswith(".xz"):
        opener = lzma.open

    if opener is None:
        analyzer.add_skip(str(path), "unsupported single-file archive")
        return

    try:
        with opener(path, "rb") as handle:
            analyzer.process_text_stream(str(path), handle, from_archive=False)
    except OSError as exc:
        analyzer.add_skip(str(path), f"archive read failure: {exc}")


def scan_zip(path: Path, analyzer: Analyzer) -> None:
    try:
        with zipfile.ZipFile(path) as archive:
            for member in sorted(archive.infolist(), key=lambda item: item.filename):
                if member.is_dir():
                    continue
                if not looks_like_log_candidate(member.filename):
                    continue
                with archive.open(member, "r") as handle:
                    analyzer.process_text_stream(f"{path}!{member.filename}", handle, from_archive=True)
    except zipfile.BadZipFile:
        analyzer.add_skip(str(path), "invalid zip archive")


def scan_tar(path: Path, analyzer: Analyzer) -> None:
    try:
        with tarfile.open(path) as archive:
            members = sorted((member for member in archive.getmembers() if member.isfile()), key=lambda item: item.name)
            for member in members:
                if not looks_like_log_candidate(member.name):
                    continue
                extracted = archive.extractfile(member)
                if extracted is None:
                    continue
                try:
                    analyzer.process_text_stream(f"{path}!{member.name}", extracted, from_archive=True)
                finally:
                    extracted.close()
    except tarfile.TarError:
        analyzer.add_skip(str(path), "invalid tar archive")


def scan_path(path: Path, analyzer: Analyzer) -> None:
    lowered = path.name.lower()

    if any(lowered.endswith(suffix) for suffix in UNSUPPORTED_ARCHIVES):
        analyzer.add_skip(str(path), "unsupported archive format")
        return

    if any(lowered.endswith(suffix) for suffix in MULTI_FILE_ARCHIVES):
        if lowered.endswith(".zip"):
            scan_zip(path, analyzer)
        else:
            scan_tar(path, analyzer)
        return

    if any(lowered.endswith(suffix) for suffix in SINGLE_FILE_COMPRESSED):
        scan_single_file_archive(path, analyzer)
        return

    scan_plain_file(path, analyzer)


def collect_candidate_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root]

    files = sorted(path for path in root.rglob("*") if path.is_file())
    candidates = [path for path in files if looks_like_log_candidate(path.name)]
    return candidates or files


def emit_text_report(report: dict[str, object], limit: int) -> None:
    summary = report["summary"]
    print(f"Input: {report['input_path']}")
    print(
        "Scanned "
        f"{summary['sources_scanned']} sources "
        f"({summary['files_scanned']} files, {summary['archive_members_scanned']} archive members), "
        f"{summary['total_lines']} lines, {summary['total_events']} events."
    )
    print()

    print("Levels:")
    for row in report["levels"]:
        print(f"- {row['level']}: {row['count']}")
    print()

    print("Top messages:")
    for item in report["top_messages"][:limit]:
        print(f"- {item['count']}x {item['pattern']}")
        print(f"  sample: {item['sample_message']}")
    print()

    print("Exception types:")
    for row in report["exception_types"][:limit]:
        print(f"- {row['type']}: {row['count']}")
    print()

    skipped = report["skipped_inputs"]
    if skipped:
        print("Skipped inputs:")
        for item in skipped:
            print(f"- {item['source']}: {item['reason']}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize repeated log messages and exceptions.")
    parser.add_argument("input_path", help="Log file or directory to analyze")
    parser.add_argument("--top", type=int, default=20, help="Maximum rows per section")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    root = Path(args.input_path).expanduser().resolve()
    if not root.exists():
        print(f"Input path does not exist: {root}", file=sys.stderr)
        return 1

    analyzer = Analyzer(limit=max(args.top, 1))
    for candidate in collect_candidate_files(root):
        scan_path(candidate, analyzer)

    report = analyzer.build_report(root)
    if args.json:
        json.dump(report, sys.stdout, indent=2, ensure_ascii=False)
        print()
    else:
        emit_text_report(report, limit=max(args.top, 1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
