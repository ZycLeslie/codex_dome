#!/usr/bin/env python3
"""Summarize JVM memory artifacts without external dependencies."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
import re
import sys
from typing import Any


HISTO_HEADER_RE = re.compile(r"#instances\s+#bytes\s+class", re.IGNORECASE)
HISTO_ROW_RE = re.compile(r"^\s*(\d+):?\s+([0-9][0-9,]*)\s+([0-9][0-9,]*)\s+(.+?)\s*$")
HISTO_TOTAL_RE = re.compile(r"^\s*Total\s+([0-9][0-9,]*)\s+([0-9][0-9,]*)\s*$", re.IGNORECASE)
HOTSPOT_STATE_RE = re.compile(r"java\.lang\.Thread\.State:\s+([A-Z_]+)")
OPENJ9_STATE_RE = re.compile(r"\bstate:([A-Z]+)\b")
SECTION_RE = re.compile(r"^0SECTION\s+(.+?)\s*$")
FLAG_RE = re.compile(r"-(?:Xmx|Xms|Xmn|Xss)\S+|-XX:[+-]?[A-Za-z0-9_.:=/-]+")
KEY_VALUE_NUM_RE = re.compile(r"^\s*([A-Za-z0-9_.:/-]+)\s*[:=]?\s+(-?\d+)\s*$")
DF_USE_RE = re.compile(r"(\d+)%$")
TOP_PID_HEADER_RE = re.compile(r"^\s*PID\s+USER\s+", re.IGNORECASE)
JAVACORE_MARKERS = (
    "0SECTION",
    "1TISIGINFO",
    "3XMTHREADINFO",
    "Full thread dump",
    "Java HotSpot(TM)",
    "OpenJ9",
    "JVMJ9VM",
)
AUXILIARY_TYPES = {
    "cgroup_memory",
    "df",
    "jstat_gcutil",
    "lsof",
    "netstat",
    "netstat_uniq",
    "ps",
    "ps_threads",
    "top",
}
AUXILIARY_LABELS = {
    "cgroup_memory": "cgroup/container memory",
    "df": "disk usage",
    "jstat_gcutil": "jstat GC utilization",
    "lsof": "open files/sockets",
    "netstat": "network sockets",
    "netstat_uniq": "aggregated network sockets",
    "ps": "process snapshot",
    "ps_threads": "process/thread snapshot",
    "top": "top snapshot",
}
CORE_SUFFIXES = {".core", ".dmp", ".dump"}


def human_size(num: int | None) -> str:
    if num is None:
        return ""
    value = float(num)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024.0 or unit == "TB":
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{num} B"


def parse_int(text: str) -> int:
    return int(text.replace(",", ""))


def mtime_iso(path: Path) -> str:
    return dt.datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")


def walk_inputs(inputs: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in inputs:
        path = Path(raw).expanduser()
        if path.is_dir():
            for child in path.rglob("*"):
                if child.is_file():
                    files.append(child)
        elif path.is_file():
            files.append(path)
        else:
            files.append(path)
    return sorted(files, key=lambda p: str(p))


def safe_read_head(path: Path, size: int = 65536) -> bytes:
    try:
        with path.open("rb") as fh:
            return fh.read(size)
    except OSError:
        return b""


def is_probable_text(head: bytes) -> bool:
    if not head:
        return True
    if b"\x00" in head[:512]:
        return False
    textish = sum(1 for b in head[:512] if b in b"\n\r\t" or 32 <= b <= 126)
    return textish / max(1, min(len(head), 512)) > 0.85


def auxiliary_kind(name: str, text: str) -> str | None:
    compact_name = name.replace("_", "-")
    lower_text = text.lower()
    if "cgroup" in compact_name or "memory.stat" in lower_text or "hierarchical_memory_limit" in lower_text:
        return "cgroup_memory"
    if "jstat" in compact_name or ("ygc" in lower_text and "fgc" in lower_text and "gct" in lower_text):
        return "jstat_gcutil"
    if "lsof" in compact_name or ("command pid user fd type" in lower_text and "node name" in lower_text):
        return "lsof"
    if "netstat" in compact_name or ("proto recv-q send-q" in lower_text and "foreign address" in lower_text):
        if "uniq" in compact_name or re.search(r"^\s*\d+\s+(tcp|udp|unix)\b", lower_text, re.MULTILINE):
            return "netstat_uniq"
        return "netstat"
    if "ps-flf" in compact_name or "ps-flf" in compact_name.replace("-l", "l"):
        return "ps_threads"
    if "ps-flf" in compact_name or "ps-flf" in compact_name.replace("-f", "f"):
        return "ps_threads"
    if "ps-fLf".lower() in name.lower() or (" lwp " in f" {lower_text} " and " nlwp " in f" {lower_text} "):
        return "ps_threads"
    if compact_name.startswith("docker-ps-") or "ps-aux" in compact_name or "ps-ef" in compact_name:
        return "ps"
    if "df-h" in compact_name or ("filesystem" in lower_text and "mounted on" in lower_text and "use%" in lower_text):
        return "df"
    if "top-" in compact_name or "top - " in lower_text or "tasks:" in lower_text and TOP_PID_HEADER_RE.search(text):
        return "top"
    return None


def artifact_kind(path: Path, head: bytes) -> str:
    name = path.name.lower()
    suffix = path.suffix.lower()
    if head.startswith(b"JAVA PROFILE ") or suffix == ".hprof" or name.endswith(".hprof"):
        return "hprof"
    if head.startswith(b"\x7fELF") or suffix in CORE_SUFFIXES and not is_probable_text(head):
        return "core_dump"
    if is_probable_text(head):
        text = head.decode("utf-8", errors="replace")
        if any(marker in text for marker in JAVACORE_MARKERS):
            return "javacore"
        if HISTO_HEADER_RE.search(text) or any(HISTO_ROW_RE.match(line) for line in text.splitlines()[:200]):
            return "histogram"
        kind = auxiliary_kind(name, text)
        if kind:
            return kind
    if "javacore" in name or ("thread" in name and suffix in {".txt", ".log", ".tdump", ".dump"}):
        return "javacore"
    if "histo" in name or "histogram" in name or "class_histogram" in name:
        return "histogram"
    kind = auxiliary_kind(name, "")
    if kind:
        return kind
    return "unknown"


def hprof_metadata(path: Path, head: bytes) -> dict[str, Any]:
    header = ""
    if head.startswith(b"JAVA PROFILE "):
        header = head.split(b"\x00", 1)[0].decode("ascii", errors="replace")
    return {
        "path": str(path),
        "type": "hprof",
        "size_bytes": path.stat().st_size,
        "size_human": human_size(path.stat().st_size),
        "modified": mtime_iso(path),
        "header": header or "not detected in first bytes",
        "note": "Binary heap dump: use MAT/VisualVM/JProfiler for retained heap and GC-root evidence.",
    }


def core_dump_metadata(path: Path, head: bytes) -> dict[str, Any]:
    header = "ELF core or binary dump" if head.startswith(b"\x7fELF") else "binary dump"
    return {
        "path": str(path),
        "type": "core_dump",
        "size_bytes": path.stat().st_size,
        "size_human": human_size(path.stat().st_size),
        "modified": mtime_iso(path),
        "header": header,
        "note": "Native/core dump: use jhsdb, gdb, or vendor tooling with the matching JDK/JVM build.",
    }


def normalize_class_name(name: str) -> str:
    name = name.strip()
    replacements = {
        "[B": "byte[]",
        "[C": "char[]",
        "[I": "int[]",
        "[J": "long[]",
        "[S": "short[]",
        "[F": "float[]",
        "[D": "double[]",
        "[Z": "boolean[]",
        "[Ljava.lang.Object;": "java.lang.Object[]",
        "[Ljava.lang.String;": "java.lang.String[]",
    }
    return replacements.get(name, name)


def class_bucket(class_name: str) -> str:
    pretty = normalize_class_name(class_name)
    if pretty.endswith("[]") or class_name.startswith("["):
        return "arrays"
    if pretty == "java.lang.String":
        return "strings"
    if "HashMap$Node" in pretty or "LinkedHashMap$Entry" in pretty or "Hashtable$Entry" in pretty:
        return "map_nodes"
    if "ConcurrentHashMap$Node" in pretty:
        return "concurrent_map_nodes"
    if "ClassLoader" in pretty or pretty == "java.lang.Class":
        return "class_metadata"
    if "DirectByteBuffer" in pretty or "MappedByteBuffer" in pretty:
        return "direct_buffers"
    if "ThreadLocal" in pretty:
        return "thread_locals"
    if pretty == "java.lang.Thread" or pretty.endswith(".Thread"):
        return "threads"
    return "other"


def parse_histogram(path: Path, top: int) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    total_instances = None
    total_bytes = None
    skipped = 0
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            total_match = HISTO_TOTAL_RE.match(line)
            if total_match:
                total_instances = parse_int(total_match.group(1))
                total_bytes = parse_int(total_match.group(2))
                continue
            match = HISTO_ROW_RE.match(line)
            if not match:
                continue
            try:
                row = {
                    "rank": int(match.group(1)),
                    "instances": parse_int(match.group(2)),
                    "bytes": parse_int(match.group(3)),
                    "class": match.group(4).strip(),
                    "pretty_class": normalize_class_name(match.group(4)),
                }
                rows.append(row)
            except ValueError:
                skipped += 1

    by_bytes = sorted(rows, key=lambda item: item["bytes"], reverse=True)
    by_instances = sorted(rows, key=lambda item: item["instances"], reverse=True)
    if total_bytes is None:
        total_bytes = sum(item["bytes"] for item in rows)
    if total_instances is None:
        total_instances = sum(item["instances"] for item in rows)

    buckets: dict[str, dict[str, int]] = {}
    for row in rows:
        bucket = class_bucket(row["class"])
        entry = buckets.setdefault(bucket, {"bytes": 0, "instances": 0, "classes": 0})
        entry["bytes"] += row["bytes"]
        entry["instances"] += row["instances"]
        entry["classes"] += 1

    signals = histogram_signals(by_bytes, buckets, total_bytes or 0)
    return {
        "path": str(path),
        "type": "histogram",
        "size_bytes": path.stat().st_size,
        "modified": mtime_iso(path),
        "row_count": len(rows),
        "skipped_rows": skipped,
        "total_instances": total_instances,
        "total_bytes": total_bytes,
        "total_human": human_size(total_bytes),
        "top_by_bytes": by_bytes[:top],
        "top_by_instances": by_instances[:top],
        "buckets": buckets,
        "signals": signals,
    }


def pct(value: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(value * 100.0 / total, 2)


def histogram_signals(rows: list[dict[str, Any]], buckets: dict[str, dict[str, int]], total_bytes: int) -> list[str]:
    signals: list[str] = []
    for bucket, label in (
        ("arrays", "arrays dominate shallow heap; inspect payload owners in HPROF"),
        ("strings", "many strings; check duplicate strings and text/cache retention"),
        ("map_nodes", "map nodes are prominent; inspect cache/map owners"),
        ("concurrent_map_nodes", "ConcurrentHashMap nodes are prominent; inspect shared caches or registries"),
        ("class_metadata", "class metadata/classloaders are prominent; check classloader or dynamic-class leaks"),
        ("direct_buffers", "direct buffers are visible; check off-heap/direct memory and cleaner roots"),
        ("thread_locals", "ThreadLocal entries are visible; inspect thread-local GC roots"),
        ("threads", "Thread objects are visible; correlate with javacore thread count"),
    ):
        bytes_value = buckets.get(bucket, {}).get("bytes", 0)
        if pct(bytes_value, total_bytes) >= 10.0:
            signals.append(f"{label} ({human_size(bytes_value)}, {pct(bytes_value, total_bytes)}% of histogram bytes)")

    if rows:
        top = rows[0]
        if pct(top["bytes"], total_bytes) >= 20.0:
            signals.append(
                f"top class {top['pretty_class']} accounts for {human_size(top['bytes'])} "
                f"({pct(top['bytes'], total_bytes)}% of histogram bytes)"
            )
    return signals


def parse_javacore(path: Path, max_samples: int) -> dict[str, Any]:
    sections: list[str] = []
    oom_lines: list[str] = []
    memory_lines: list[str] = []
    blocked_samples: list[str] = []
    vm_lines: list[str] = []
    flags: list[str] = []
    thread_states: dict[str, int] = {}
    thread_count = 0
    line_count = 0

    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            line_count += 1
            line = raw.rstrip("\n")
            section_match = SECTION_RE.match(line)
            if section_match:
                sections.append(section_match.group(1).strip())

            if "OutOfMemoryError" in line or "OutOfMemory" in line or "OOM" in line or "systhrow" in line:
                append_limited(oom_lines, line.strip(), max_samples)

            lower = line.lower()
            if any(token in lower for token in ("heap", "meminfo", "native memory", "direct buffer", "metaspace")):
                if re.search(r"\d", line):
                    append_limited(memory_lines, line.strip(), max_samples)

            if any(token in line for token in ("1CIVM", "1CIJAVA", "JRE", "Java VM", "JVMJ9VM")):
                append_limited(vm_lines, line.strip(), max_samples)

            for flag in FLAG_RE.findall(line):
                if flag not in flags:
                    flags.append(flag)

            hot_state = HOTSPOT_STATE_RE.search(line)
            openj9_state = OPENJ9_STATE_RE.search(line)
            state = None
            if hot_state:
                state = hot_state.group(1)
            elif openj9_state:
                state = openj9_state.group(1)
            if state:
                thread_states[state] = thread_states.get(state, 0) + 1

            if line.startswith('"') or "3XMTHREADINFO" in line:
                thread_count += 1

            if "BLOCKED" in line or "deadlock" in lower or "monitor" in lower and "blocked" in lower:
                append_limited(blocked_samples, line.strip(), max_samples)

    signals = javacore_signals(oom_lines, memory_lines, thread_states, flags, thread_count)
    return {
        "path": str(path),
        "type": "javacore",
        "size_bytes": path.stat().st_size,
        "modified": mtime_iso(path),
        "line_count": line_count,
        "sections": sections[:30],
        "vm_lines": vm_lines,
        "jvm_flags": flags,
        "oom_lines": oom_lines,
        "memory_lines": memory_lines,
        "thread_count_estimate": thread_count,
        "thread_states": thread_states,
        "blocked_samples": blocked_samples,
        "signals": signals,
    }


def append_limited(items: list[str], value: str, limit: int) -> None:
    if value and len(items) < limit and value not in items:
        items.append(value)


def read_text_lines(path: Path, max_lines: int = 50000) -> tuple[list[str], bool]:
    lines: list[str] = []
    truncated = False
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for index, line in enumerate(fh):
            if index >= max_lines:
                truncated = True
                break
            lines.append(line.rstrip("\n"))
    return lines, truncated


def parse_float(value: str) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None


def parse_auxiliary(path: Path, kind: str, max_samples: int) -> dict[str, Any]:
    lines, truncated = read_text_lines(path)
    parsers = {
        "cgroup_memory": parse_cgroup_memory,
        "df": parse_df,
        "jstat_gcutil": parse_jstat_gcutil,
        "lsof": parse_lsof,
        "netstat": parse_netstat,
        "netstat_uniq": parse_netstat,
        "ps": parse_ps,
        "ps_threads": parse_ps_threads,
        "top": parse_top,
    }
    body = parsers.get(kind, parse_generic_auxiliary)(lines, max_samples)
    body.update(
        {
            "path": str(path),
            "type": kind,
            "label": AUXILIARY_LABELS.get(kind, kind),
            "size_bytes": path.stat().st_size,
            "modified": mtime_iso(path),
            "line_count": len(lines),
            "truncated": truncated,
        }
    )
    return body


def parse_generic_auxiliary(lines: list[str], max_samples: int) -> dict[str, Any]:
    return {
        "summary": ["unparsed auxiliary text"],
        "signals": [],
        "samples": [line for line in lines[:max_samples] if line.strip()],
    }


def parse_cgroup_memory(lines: list[str], max_samples: int) -> dict[str, Any]:
    metrics: dict[str, int] = {}
    samples: list[str] = []
    for line in lines:
        match = KEY_VALUE_NUM_RE.match(line)
        if match:
            metrics[match.group(1)] = int(match.group(2))
        elif any(token in line.lower() for token in ("memory", "oom", "failcnt", "rss", "cache")):
            append_limited(samples, line.strip(), max_samples)

    usage = first_metric(metrics, ("memory.usage_in_bytes", "memory.current", "usage_in_bytes", "usage"))
    limit = first_metric(metrics, ("memory.limit_in_bytes", "memory.max", "hierarchical_memory_limit", "limit_in_bytes", "limit"))
    rss = first_metric(metrics, ("total_rss", "rss", "anon"))
    cache = first_metric(metrics, ("total_cache", "cache", "file"))
    failcnt = first_metric(metrics, ("memory.failcnt", "failcnt"))
    oom_kill = first_metric(metrics, ("oom_kill", "oom_kill_disable", "under_oom"))
    signals: list[str] = []
    summary: list[str] = []

    if usage is not None:
        summary.append(f"container memory usage {human_size(usage)}")
    if limit is not None and limit < (1 << 60):
        summary.append(f"container memory limit {human_size(limit)}")
    if usage is not None and limit is not None and 0 < limit < (1 << 60):
        percent = pct(usage, limit)
        summary.append(f"usage is {percent}% of limit")
        if percent >= 90.0:
            signals.append(f"container memory usage is high: {percent}% of limit")
    if rss is not None:
        summary.append(f"rss {human_size(rss)}")
    if cache is not None:
        summary.append(f"cache {human_size(cache)}")
    if failcnt and failcnt > 0:
        signals.append(f"cgroup memory failcnt is {failcnt}")
    if oom_kill and oom_kill > 0:
        signals.append(f"cgroup OOM-related counter is {oom_kill}")

    return {"summary": summary, "signals": signals, "metrics": sample_metrics(metrics), "samples": samples}


def first_metric(metrics: dict[str, int], names: tuple[str, ...]) -> int | None:
    for name in names:
        if name in metrics:
            return metrics[name]
    return None


def sample_metrics(metrics: dict[str, int], limit: int = 20) -> dict[str, str]:
    sampled: dict[str, str] = {}
    for key in sorted(metrics)[:limit]:
        value = metrics[key]
        sampled[key] = f"{value} ({human_size(value)})" if abs(value) >= 1024 else str(value)
    return sampled


def parse_df(lines: list[str], max_samples: int) -> dict[str, Any]:
    mounts: list[dict[str, Any]] = []
    for line in lines:
        parts = line.split()
        if len(parts) < 6 or parts[0].lower() == "filesystem":
            continue
        use_match = DF_USE_RE.match(parts[-2])
        if not use_match:
            continue
        mounts.append({"filesystem": parts[0], "use_percent": int(use_match.group(1)), "mounted_on": parts[-1], "raw": line})
    mounts.sort(key=lambda item: item["use_percent"], reverse=True)
    signals = [f"filesystem {item['mounted_on']} is {item['use_percent']}% full" for item in mounts if item["use_percent"] >= 90]
    summary = [f"{len(mounts)} filesystems parsed"]
    if mounts:
        summary.append(f"highest disk usage {mounts[0]['use_percent']}% on {mounts[0]['mounted_on']}")
    return {"summary": summary, "signals": signals, "top_entries": mounts[:10], "samples": [m["raw"] for m in mounts[:max_samples]]}


def parse_jstat_gcutil(lines: list[str], max_samples: int) -> dict[str, Any]:
    header: list[str] = []
    rows: list[list[str]] = []
    for line in lines:
        parts = line.split()
        if not parts:
            continue
        if {"YGC", "FGC", "GCT"}.issubset(set(parts)):
            header = parts
            continue
        if header and len(parts) >= len(header):
            rows.append(parts[: len(header)])
    last: dict[str, float] = {}
    if header and rows:
        for key, value in zip(header, rows[-1]):
            parsed = parse_float(value)
            if parsed is not None:
                last[key] = parsed
    signals: list[str] = []
    for key in ("E", "O", "M", "CCS"):
        if last.get(key, 0.0) >= 90.0:
            signals.append(f"jstat {key} utilization is high: {last[key]}%")
    if last.get("FGC", 0.0) > 0:
        signals.append(f"full GC count observed: {int(last['FGC'])}")
    summary = [f"{len(rows)} jstat samples parsed"]
    if last:
        summary.append(", ".join(f"{key}={value:g}" for key, value in last.items() if key in {"E", "O", "M", "CCS", "YGC", "FGC", "GCT"}))
    return {"summary": summary, "signals": signals, "last_sample": last, "samples": lines[:max_samples]}


def parse_lsof(lines: list[str], max_samples: int) -> dict[str, Any]:
    total = 0
    deleted = 0
    type_counts: dict[str, int] = {}
    fd_samples: list[str] = []
    for line in lines:
        if not line.strip() or line.startswith("COMMAND "):
            continue
        parts = line.split(None, 8)
        if len(parts) < 5:
            continue
        total += 1
        type_counts[parts[4]] = type_counts.get(parts[4], 0) + 1
        if "deleted" in line.lower():
            deleted += 1
            append_limited(fd_samples, line.strip(), max_samples)
    signals: list[str] = []
    if total >= 5000:
        signals.append(f"high open file descriptor count: {total}")
    if deleted:
        signals.append(f"{deleted} deleted-but-open files observed")
    socket_count = sum(count for typ, count in type_counts.items() if typ in {"IPv4", "IPv6", "unix", "sock"} or "sock" in typ.lower())
    if socket_count >= 1000:
        signals.append(f"high open socket count in lsof: {socket_count}")
    summary = [f"{total} open file/socket rows parsed"]
    return {"summary": summary, "signals": signals, "type_counts": type_counts, "samples": fd_samples or lines[:max_samples]}


def parse_netstat(lines: list[str], max_samples: int) -> dict[str, Any]:
    state_counts: dict[str, int] = {}
    proto_counts: dict[str, int] = {}
    samples: list[str] = []
    for line in lines:
        parts = line.split()
        if not parts or parts[0].lower() == "proto":
            continue
        count = 1
        proto_index = 0
        if parts[0].isdigit() and len(parts) > 1:
            count = int(parts[0])
            proto_index = 1
        proto = parts[proto_index].lower()
        if not (proto.startswith("tcp") or proto.startswith("udp") or proto == "unix"):
            continue
        proto_counts[proto] = proto_counts.get(proto, 0) + count
        state = "UNKNOWN"
        for token in reversed(parts):
            if token in {"ESTABLISHED", "LISTEN", "TIME_WAIT", "CLOSE_WAIT", "SYN_SENT", "SYN_RECV", "FIN_WAIT1", "FIN_WAIT2", "LAST_ACK"}:
                state = token
                break
        state_counts[state] = state_counts.get(state, 0) + count
        if state in {"CLOSE_WAIT", "SYN_SENT", "SYN_RECV"}:
            append_limited(samples, line.strip(), max_samples)
    signals: list[str] = []
    for state, threshold in (("CLOSE_WAIT", 100), ("ESTABLISHED", 10000), ("TIME_WAIT", 10000), ("SYN_RECV", 1000)):
        if state_counts.get(state, 0) >= threshold:
            signals.append(f"many {state} sockets: {state_counts[state]}")
    summary = [", ".join(f"{state}={count}" for state, count in sorted(state_counts.items()))] if state_counts else []
    return {"summary": summary, "signals": signals, "state_counts": state_counts, "proto_counts": proto_counts, "samples": samples}


def parse_ps(lines: list[str], max_samples: int) -> dict[str, Any]:
    java_commands: list[str] = []
    jvm_flags: list[str] = []
    top_rss: list[dict[str, Any]] = []
    for line in lines:
        if not line.strip() or line.startswith(("USER ", "UID ")):
            continue
        lower = line.lower()
        if "java" in lower:
            append_limited(java_commands, line.strip(), max_samples)
            for flag in FLAG_RE.findall(line):
                if flag not in jvm_flags:
                    jvm_flags.append(flag)
        parts = line.split(None, 10)
        if len(parts) >= 11 and parts[1].isdigit():
            rss = parse_int_if_possible(parts[5])
            mem_percent = parse_float(parts[3])
            if rss is not None:
                top_rss.append({"pid": parts[1], "rss_kb": rss, "mem_percent": mem_percent, "command": parts[10][:180]})
    top_rss.sort(key=lambda item: item["rss_kb"], reverse=True)
    signals = ["java process command line found"] if java_commands else []
    if top_rss and "java" in top_rss[0]["command"].lower():
        signals.append(f"java process has highest parsed RSS: {human_size(top_rss[0]['rss_kb'] * 1024)}")
    summary = [f"{len(java_commands)} java command samples found"]
    return {"summary": summary, "signals": signals, "jvm_flags": jvm_flags, "top_rss": top_rss[:10], "samples": java_commands}


def parse_int_if_possible(value: str) -> int | None:
    try:
        return int(value)
    except ValueError:
        return None


def parse_ps_threads(lines: list[str], max_samples: int) -> dict[str, Any]:
    threads_by_pid: dict[str, int] = {}
    java_samples: list[str] = []
    for line in lines:
        if not line.strip() or line.startswith(("UID ", "USER ")):
            continue
        parts = line.split(None, 10)
        if len(parts) < 4:
            continue
        pid = parts[1] if parts[1].isdigit() else ""
        if pid:
            current_threads = threads_by_pid.get(pid, 0)
            nlwp = parse_int_if_possible(parts[5]) if len(parts) > 5 else None
            if nlwp is not None:
                threads_by_pid[pid] = max(current_threads, nlwp)
            else:
                threads_by_pid[pid] = current_threads + 1
        if "java" in line.lower():
            append_limited(java_samples, line.strip(), max_samples)
    top_threads = sorted(threads_by_pid.items(), key=lambda item: item[1], reverse=True)[:10]
    signals: list[str] = []
    if top_threads and top_threads[0][1] >= 500:
        signals.append(f"high thread/LWP count for pid {top_threads[0][0]}: {top_threads[0][1]}")
    summary = [f"{len(threads_by_pid)} PIDs with thread rows parsed"]
    return {"summary": summary, "signals": signals, "top_threads": [{"pid": pid, "threads": count} for pid, count in top_threads], "samples": java_samples}


def parse_top(lines: list[str], max_samples: int) -> dict[str, Any]:
    memory_lines: list[str] = []
    process_rows: list[str] = []
    in_process_table = False
    for line in lines:
        lower = line.lower()
        if "mem" in lower or "swap" in lower or "%cpu" in lower or "load average" in lower:
            append_limited(memory_lines, line.strip(), max_samples)
        if TOP_PID_HEADER_RE.search(line):
            in_process_table = True
            continue
        if in_process_table and line.strip():
            process_rows.append(line.strip())
    java_rows = [row for row in process_rows if "java" in row.lower()]
    signals = ["java process/thread visible in top snapshot"] if java_rows else []
    summary = [f"{len(process_rows)} top process/thread rows parsed"]
    return {"summary": summary, "signals": signals, "samples": memory_lines + java_rows[:max_samples]}


def javacore_signals(
    oom_lines: list[str],
    memory_lines: list[str],
    thread_states: dict[str, int],
    flags: list[str],
    thread_count: int,
) -> list[str]:
    text = "\n".join(oom_lines + memory_lines + flags).lower()
    signals: list[str] = []
    if "java heap space" in text:
        signals.append("Java heap OOM marker found")
    if "gc overhead" in text:
        signals.append("GC overhead limit marker found")
    if "metaspace" in text or "compressed class space" in text:
        signals.append("metaspace/class-space pressure marker found")
    if "direct buffer memory" in text or "directbytebuffer" in text:
        signals.append("direct-buffer/off-heap pressure marker found")
    if "unable to create" in text and "thread" in text:
        signals.append("native-thread creation failure marker found")
    if thread_count >= 500:
        signals.append(f"high estimated thread count: {thread_count}")
    blocked = thread_states.get("BLOCKED", 0) + thread_states.get("B", 0)
    if blocked >= 20:
        signals.append(f"many blocked threads: {blocked}")
    if any(flag.startswith("-Xss") for flag in flags) and thread_count >= 200:
        signals.append("thread stack size plus high thread count may contribute to native memory pressure")
    return signals


def analyze_file(path: Path, top: int, max_samples: int, forced_type: str) -> dict[str, Any]:
    if not path.exists():
        return {"path": str(path), "type": "missing", "error": "path does not exist"}
    head = safe_read_head(path)
    kind = forced_type if forced_type != "auto" else artifact_kind(path, head)
    try:
        if kind == "hprof":
            return hprof_metadata(path, head)
        if kind == "core_dump":
            return core_dump_metadata(path, head)
        if kind == "histogram":
            return parse_histogram(path, top)
        if kind == "javacore":
            return parse_javacore(path, max_samples)
        if kind in AUXILIARY_TYPES:
            return parse_auxiliary(path, kind, max_samples)
        return {
            "path": str(path),
            "type": "unknown",
            "size_bytes": path.stat().st_size,
            "modified": mtime_iso(path),
            "note": "Not recognized as HPROF, histogram, or javacore/thread dump.",
        }
    except UnicodeDecodeError as exc:
        return {"path": str(path), "type": kind, "error": f"text decode failed: {exc}"}
    except OSError as exc:
        return {"path": str(path), "type": kind, "error": str(exc)}


def build_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    signals: list[dict[str, str]] = []
    for item in results:
        kind = item.get("type", "unknown")
        counts[kind] = counts.get(kind, 0) + 1
        for signal in item.get("signals", []) or []:
            signals.append({"path": item.get("path", ""), "signal": signal})
    return {
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "artifact_counts": counts,
        "signals": signals,
    }


def markdown_table_row(values: list[Any]) -> str:
    return "| " + " | ".join(str(value).replace("\n", " ") for value in values) + " |"


def to_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# JVM Memory Artifact Summary")
    lines.append("")
    lines.append(f"Generated: {payload['summary']['generated_at']}")
    lines.append("")
    lines.append("## Inputs")
    lines.append("")
    lines.append("| Type | Path | Size | Modified | Notes |")
    lines.append("| --- | --- | ---: | --- | --- |")
    for item in payload["artifacts"]:
        notes = item.get("error") or item.get("note") or ", ".join(item.get("signals", [])[:2])
        lines.append(
            markdown_table_row(
                [
                    item.get("type", ""),
                    item.get("path", ""),
                    human_size(item.get("size_bytes")) if item.get("size_bytes") is not None else "",
                    item.get("modified", ""),
                    notes,
                ]
            )
        )

    dump_files = [item for item in payload["artifacts"] if item.get("type") in {"hprof", "core_dump"}]
    if dump_files:
        lines.extend(["", "## Dump Files", ""])
        for item in dump_files:
            lines.append(f"- `{item['path']}`: {item.get('size_human')} header={item.get('header')!r}")
        lines.append("")
        lines.append("Use MAT/VisualVM/JProfiler for HPROF retained heap. Use jhsdb/gdb/vendor tooling for native core dumps.")

    histograms = [item for item in payload["artifacts"] if item.get("type") == "histogram"]
    for item in histograms:
        lines.extend(["", f"## Histogram: `{item['path']}`", ""])
        lines.append(
            f"Rows: {item.get('row_count', 0)}, total shallow bytes: {item.get('total_human')} "
            f"({item.get('total_instances', 0)} instances)"
        )
        if item.get("signals"):
            lines.append("")
            lines.append("Signals:")
            for signal in item["signals"]:
                lines.append(f"- {signal}")
        lines.extend(["", "| Rank | Bytes | Instances | Class |", "| ---: | ---: | ---: | --- |"])
        for row in item.get("top_by_bytes", []):
            lines.append(markdown_table_row([row["rank"], human_size(row["bytes"]), row["instances"], row["pretty_class"]]))

    javacores = [item for item in payload["artifacts"] if item.get("type") == "javacore"]
    for item in javacores:
        lines.extend(["", f"## Javacore/Thread Dump: `{item['path']}`", ""])
        lines.append(f"Lines: {item.get('line_count', 0)}, estimated threads: {item.get('thread_count_estimate', 0)}")
        if item.get("signals"):
            lines.append("")
            lines.append("Signals:")
            for signal in item["signals"]:
                lines.append(f"- {signal}")
        if item.get("jvm_flags"):
            lines.extend(["", "JVM flags:"])
            lines.append("`" + " ".join(item["jvm_flags"][:40]) + "`")
        if item.get("thread_states"):
            lines.extend(["", "Thread states:"])
            for state, count in sorted(item["thread_states"].items(), key=lambda kv: (-kv[1], kv[0])):
                lines.append(f"- {state}: {count}")
        if item.get("oom_lines"):
            lines.extend(["", "OOM/event samples:"])
            for sample in item["oom_lines"]:
                lines.append(f"- `{sample[:240]}`")
        if item.get("memory_lines"):
            lines.extend(["", "Memory samples:"])
            for sample in item["memory_lines"][:10]:
                lines.append(f"- `{sample[:240]}`")

    auxiliaries = [item for item in payload["artifacts"] if item.get("type") in AUXILIARY_TYPES]
    if auxiliaries:
        lines.extend(["", "## Auxiliary System Evidence", ""])
        for item in auxiliaries:
            lines.extend(["", f"### {item.get('label', item.get('type'))}: `{item['path']}`", ""])
            if item.get("summary"):
                for summary in item["summary"]:
                    lines.append(f"- {summary}")
            if item.get("signals"):
                lines.append("")
                lines.append("Signals:")
                for signal in item["signals"]:
                    lines.append(f"- {signal}")
            if item.get("jvm_flags"):
                lines.append("")
                lines.append("JVM flags:")
                lines.append("`" + " ".join(item["jvm_flags"][:40]) + "`")
            if item.get("top_threads"):
                lines.extend(["", "| PID | Threads |", "| --- | ---: |"])
                for entry in item["top_threads"]:
                    lines.append(markdown_table_row([entry["pid"], entry["threads"]]))
            if item.get("top_rss"):
                lines.extend(["", "| PID | RSS | %MEM | Command |", "| --- | ---: | ---: | --- |"])
                for entry in item["top_rss"][:5]:
                    lines.append(
                        markdown_table_row(
                            [
                                entry["pid"],
                                human_size(entry["rss_kb"] * 1024),
                                entry.get("mem_percent", ""),
                                entry["command"],
                            ]
                        )
                    )
            if item.get("samples"):
                lines.append("")
                lines.append("Samples:")
                for sample in item["samples"][:8]:
                    lines.append(f"- `{sample[:240]}`")

    if payload["summary"].get("signals"):
        lines.extend(["", "## Cross-Artifact Signals", ""])
        for signal in payload["summary"]["signals"]:
            lines.append(f"- `{signal['path']}`: {signal['signal']}")

    lines.extend(
        [
            "",
            "## Next Diagnostics",
            "",
            "- Start from the dump retained-heap/core analysis, then use auxiliary files to explain limits, threads, native memory, sockets, and capture completeness.",
            "- Compare multiple histograms/javacores/system snapshots by timestamp when available.",
            "- Correlate with GC logs, JVM flags, cgroup limits, process RSS, thread counts, file descriptors, and the exact OOM or kill event.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Summarize JVM HPROF, class histogram, javacore, and thread dump artifacts.")
    parser.add_argument("inputs", nargs="+", help="Files or directories to scan")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--out", help="Write output to this file instead of stdout")
    parser.add_argument(
        "--type",
        choices=("auto", "hprof", "core_dump", "histogram", "javacore", *sorted(AUXILIARY_TYPES)),
        default="auto",
        help="Override artifact type for all scanned files when filenames or content are ambiguous",
    )
    parser.add_argument("--top", type=int, default=20, help="Top histogram rows to include")
    parser.add_argument("--max-samples", type=int, default=20, help="Maximum javacore sample lines per category")
    args = parser.parse_args(argv)

    files = walk_inputs(args.inputs)
    artifacts = [analyze_file(path, args.top, args.max_samples, args.type) for path in files]
    payload = {"summary": build_summary(artifacts), "artifacts": artifacts}
    if args.format == "json":
        output = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    else:
        output = to_markdown(payload)

    if args.out:
        out = Path(args.out).expanduser()
        out.write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
