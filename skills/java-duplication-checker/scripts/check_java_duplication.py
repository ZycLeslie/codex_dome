#!/usr/bin/env python3
"""Find duplicated Java classes/methods and provide behavior-safe reduction advice."""

from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass, fields
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Set, Tuple, Type, TypeVar

CACHE_VERSION = 2

JAVA_KEYWORDS = {
    "abstract",
    "assert",
    "boolean",
    "break",
    "byte",
    "case",
    "catch",
    "char",
    "class",
    "const",
    "continue",
    "default",
    "do",
    "double",
    "else",
    "enum",
    "extends",
    "final",
    "finally",
    "float",
    "for",
    "goto",
    "if",
    "implements",
    "import",
    "instanceof",
    "int",
    "interface",
    "long",
    "native",
    "new",
    "package",
    "private",
    "protected",
    "public",
    "record",
    "return",
    "short",
    "static",
    "strictfp",
    "super",
    "switch",
    "synchronized",
    "this",
    "throw",
    "throws",
    "transient",
    "try",
    "var",
    "void",
    "volatile",
    "while",
    "yield",
}

METHOD_CONTROL_KEYWORDS = {"if", "for", "while", "switch", "catch", "do", "try", "else"}
METHOD_MODIFIERS = {
    "public",
    "protected",
    "private",
    "static",
    "final",
    "abstract",
    "native",
    "synchronized",
    "default",
    "strictfp",
}

SIDE_EFFECT_HINTS = (
    "repository.",
    "entitymanager",
    "jdbc",
    "resttemplate",
    "webclient",
    "http",
    "kafka",
    "rabbit",
    "redis",
    "files.",
    "fileoutputstream",
    "socket",
    "send(",
    "publish(",
    "insert(",
    "update(",
    "delete(",
    "save(",
)

TOKEN_RE = re.compile(
    r"[A-Za-z_][A-Za-z0-9_]*|\d+\.\d+|\d+|==|!=|<=|>=|&&|\|\||::|->|[{}()\[\].,;:+\-*/%<>=!&|^~?]"
)
IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*$")
NUMBER_RE = re.compile(r"\d+(?:\.\d+)?$")
CLASS_DECL_RE = re.compile(r"\b(class|interface|enum|record)\s+([A-Za-z_][A-Za-z0-9_]*)\b")
PACKAGE_RE = re.compile(r"^\s*package\s+([A-Za-z_][A-Za-z0-9_.]*)\s*;", re.MULTILINE)

T = TypeVar("T")


@dataclass
class JavaClassInfo:
    uid: str
    file: str
    package: str
    name: str
    kind: str
    start_line: int
    end_line: int
    line_count: int
    token_count: int
    generalized: str
    hash_exact: str


@dataclass
class JavaMethodInfo:
    uid: str
    file: str
    package: str
    class_name: str
    method_name: str
    signature: str
    modifiers: List[str]
    start_line: int
    end_line: int
    line_count: int
    token_count: int
    generalized: str
    hash_exact: str
    risk_level: str
    risk_reasons: List[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Detect duplicated Java classes/methods and emit safe deduplication advice."
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root path to scan (clone or checkout remote repositories first).",
    )
    parser.add_argument(
        "--ignore-dir",
        action="append",
        default=[],
        help="Directory names to ignore (repeatable).",
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Include src/test and *Test.java files (default: excluded).",
    )
    parser.add_argument("--min-class-lines", type=int, default=30)
    parser.add_argument("--min-method-lines", type=int, default=6)
    parser.add_argument("--min-class-tokens", type=int, default=120)
    parser.add_argument("--min-method-tokens", type=int, default=30)
    parser.add_argument("--similarity-threshold", type=float, default=0.90)
    parser.add_argument(
        "--max-comparisons",
        type=int,
        default=50000,
        help="Upper bound for fuzzy pair comparisons to keep runtime predictable.",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Emit compact group summaries; combine with --group-id to expand specific groups.",
    )
    parser.add_argument(
        "--group-id",
        action="append",
        default=[],
        help="Group id(s) to expand when --summary-only is enabled (repeatable).",
    )
    parser.add_argument(
        "--cache-file",
        default=".java-dup-cache.json",
        help="Cache file path for incremental scan (default: <root>/.java-dup-cache.json).",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable incremental cache and parse all Java files from source.",
    )
    parser.add_argument(
        "--refresh-cache",
        action="store_true",
        help="Ignore existing cache once and rebuild cache from source files.",
    )
    parser.add_argument("--output", help="Optional JSON output path.")
    return parser.parse_args()


def build_line_starts(text: str) -> List[int]:
    starts = [0]
    for index, char in enumerate(text):
        if char == "\n":
            starts.append(index + 1)
    return starts


def line_number(line_starts: Sequence[int], index: int) -> int:
    return bisect.bisect_right(line_starts, index)


def sha1(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def dataclass_from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
    cls_fields = {item.name for item in fields(cls)}
    payload = {key: value for key, value in data.items() if key in cls_fields}
    return cls(**payload)


def mask_non_code(source: str) -> str:
    """Mask strings/comments with spaces while preserving length and newlines."""
    output: List[str] = []
    i = 0
    n = len(source)
    state = "code"

    while i < n:
        char = source[i]
        nxt = source[i + 1] if i + 1 < n else ""

        if state == "code":
            if char == "/" and nxt == "/":
                output.extend([" ", " "])
                i += 2
                state = "line_comment"
                continue
            if char == "/" and nxt == "*":
                output.extend([" ", " "])
                i += 2
                state = "block_comment"
                continue
            if source.startswith('"""', i):
                output.extend([" ", " ", " "])
                i += 3
                state = "text_block"
                continue
            if char == '"':
                output.append(" ")
                i += 1
                state = "string"
                continue
            if char == "'":
                output.append(" ")
                i += 1
                state = "char"
                continue
            output.append(char)
            i += 1
            continue

        if state == "line_comment":
            if char == "\n":
                output.append("\n")
                i += 1
                state = "code"
            else:
                output.append(" ")
                i += 1
            continue

        if state == "block_comment":
            if char == "*" and nxt == "/":
                output.extend([" ", " "])
                i += 2
                state = "code"
            else:
                output.append("\n" if char == "\n" else " ")
                i += 1
            continue

        if state == "string":
            if char == "\\" and i + 1 < n:
                output.extend([" ", " "])
                i += 2
            elif char == '"':
                output.append(" ")
                i += 1
                state = "code"
            else:
                output.append("\n" if char == "\n" else " ")
                i += 1
            continue

        if state == "char":
            if char == "\\" and i + 1 < n:
                output.extend([" ", " "])
                i += 2
            elif char == "'":
                output.append(" ")
                i += 1
                state = "code"
            else:
                output.append("\n" if char == "\n" else " ")
                i += 1
            continue

        if state == "text_block":
            if source.startswith('"""', i):
                output.extend([" ", " ", " "])
                i += 3
                state = "code"
            else:
                output.append("\n" if char == "\n" else " ")
                i += 1
            continue

    return "".join(output)


def tokenize(code_text: str) -> List[str]:
    return TOKEN_RE.findall(code_text)


def normalize_tokens(tokens: Sequence[str]) -> str:
    return " ".join(tokens)


def generalize_tokens(tokens: Sequence[str]) -> str:
    generalized: List[str] = []
    for token in tokens:
        if token in JAVA_KEYWORDS:
            generalized.append(token)
        elif NUMBER_RE.match(token):
            generalized.append("NUM")
        elif IDENT_RE.match(token):
            generalized.append("ID")
        else:
            generalized.append(token)
    return " ".join(generalized)


def find_java_files(root: Path, ignore_dirs: Sequence[str], include_tests: bool) -> List[Path]:
    default_ignored = {
        ".git",
        ".idea",
        ".gradle",
        ".mvn",
        "build",
        "target",
        "out",
        "node_modules",
    }
    ignored = default_ignored | set(ignore_dirs)

    java_files: List[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in ignored]
        for filename in filenames:
            if not filename.endswith(".java"):
                continue
            full_path = Path(dirpath) / filename
            rel = full_path.relative_to(root)
            rel_text = str(rel).replace("\\", "/")
            if not include_tests:
                if rel_text.startswith("src/test/") or filename.endswith("Test.java") or filename.endswith("Tests.java"):
                    continue
            java_files.append(full_path)
    return sorted(java_files)


def find_matching_brace(masked: str, opening_index: int) -> int:
    depth = 0
    for index in range(opening_index, len(masked)):
        char = masked[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
    return -1


def find_member_start(masked: str, min_index: int, brace_index: int) -> int:
    index = brace_index - 1
    while index >= min_index and masked[index].isspace():
        index -= 1
    while index >= min_index:
        if masked[index] in "{};":
            return index + 1
        index -= 1
    return min_index


def extract_method_name(header_text: str) -> str:
    open_paren = header_text.rfind("(")
    if open_paren == -1:
        return ""
    prefix = header_text[:open_paren]
    match = re.search(r"([A-Za-z_][A-Za-z0-9_]*)\s*$", prefix)
    if not match:
        return ""
    return match.group(1)


def looks_like_method_header(header_text: str, method_name: str) -> bool:
    compact = " ".join(header_text.split())
    if not compact:
        return False
    if "(" not in compact or ")" not in compact:
        return False
    if "->" in compact:
        return False
    if method_name in METHOD_CONTROL_KEYWORDS:
        return False
    if re.search(r"\b(class|interface|enum|record)\b", compact):
        return False
    if re.search(r"\b(if|for|while|switch|catch|try|do)\s*\(", compact):
        return False
    if compact.startswith("new "):
        return False

    open_paren = compact.find("(")
    prefix = compact[:open_paren]
    if "=" in prefix:
        return False

    if compact.startswith("synchronized(") or compact.startswith("synchronized ("):
        return False
    if compact.startswith("static {"):
        return False

    return True


def extract_modifiers(header_text: str) -> List[str]:
    words = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", header_text)
    return sorted({word for word in words if word in METHOD_MODIFIERS})


def unique(items: Iterable[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def assess_method_risk(signature: str, body: str, modifiers: Sequence[str]) -> Tuple[str, List[str]]:
    reasons: List[str] = []
    score = 0

    signature_text = signature
    body_text = body
    signature_lower = signature_text.lower()
    body_lower = body_text.lower()

    if re.search(r"\bthis\.[A-Za-z_][A-Za-z0-9_]*\s*(=|\+=|-=|\*=|/=|%=|\+\+|--)", body_text):
        score = max(score, 2)
        reasons.append("写入实例字段，状态变更风险高")
    elif "this." in body_text or "super." in body_text:
        score = max(score, 1)
        reasons.append("依赖实例状态或父类行为")

    if re.search(r"\b(throw|throws)\b", signature_text + "\n" + body_text):
        score = max(score, 1)
        reasons.append("包含异常语义，重构后需保持异常契约")

    if re.search(
        r"@Transactional|@Cacheable|@CacheEvict|@Retryable|@Async|@CircuitBreaker|@Secured|@PreAuthorize",
        signature_text,
    ):
        score = max(score, 2)
        reasons.append("存在框架注解，迁移位置可能影响运行时行为")

    if "synchronized" in signature_lower or re.search(r"\bsynchronized\s*\(", body_text):
        score = max(score, 2)
        reasons.append("涉及并发同步")

    matched_side_effects = [hint for hint in SIDE_EFFECT_HINTS if hint in body_lower]
    if matched_side_effects:
        score = max(score, 2 if len(matched_side_effects) >= 2 else 1)
        reasons.append(
            "可能包含外部副作用调用: " + ", ".join(matched_side_effects[:4])
        )

    if "public" in modifiers or "protected" in modifiers:
        score = max(score, 1)
        reasons.append("对外可见方法，兼容性要求更高")

    if score <= 0:
        return "low", ["未发现明显副作用信号，可优先按低风险路径处理"]
    if score == 1:
        return "medium", unique(reasons)
    return "high", unique(reasons)


def extract_classes_and_methods(
    root: Path,
    java_file: Path,
    min_class_lines: int,
    min_method_lines: int,
) -> Tuple[List[JavaClassInfo], List[JavaMethodInfo]]:
    source = java_file.read_text(encoding="utf-8", errors="replace")
    masked = mask_non_code(source)
    line_starts = build_line_starts(source)

    package_match = PACKAGE_RE.search(masked)
    package_name = package_match.group(1) if package_match else ""
    relative_path = str(java_file.relative_to(root)).replace("\\", "/")

    class_infos: List[JavaClassInfo] = []
    class_scopes: List[Tuple[JavaClassInfo, int, int]] = []
    methods: List[JavaMethodInfo] = []

    for match in CLASS_DECL_RE.finditer(masked):
        kind = match.group(1)
        class_name = match.group(2)

        brace_open = masked.find("{", match.end())
        if brace_open == -1:
            continue
        semicolon_before_brace = masked.find(";", match.end(), brace_open)
        if semicolon_before_brace != -1:
            continue

        brace_close = find_matching_brace(masked, brace_open)
        if brace_close == -1:
            continue

        class_tokens = tokenize(masked[brace_open + 1 : brace_close])
        start_line = line_number(line_starts, match.start())
        end_line = line_number(line_starts, brace_close)
        line_count = max(1, end_line - start_line + 1)

        if line_count >= min_class_lines and class_tokens:
            normalized = normalize_tokens(class_tokens)
            class_info = JavaClassInfo(
                uid=f"{relative_path}:{class_name}:{start_line}",
                file=relative_path,
                package=package_name,
                name=class_name,
                kind=kind,
                start_line=start_line,
                end_line=end_line,
                line_count=line_count,
                token_count=len(class_tokens),
                generalized=generalize_tokens(class_tokens),
                hash_exact=sha1(normalized),
            )
            class_infos.append(class_info)
            class_scopes.append((class_info, brace_open, brace_close))

    for class_info, class_open, class_close in class_scopes:
        cursor = class_open + 1
        while cursor < class_close:
            brace_index = masked.find("{", cursor, class_close)
            if brace_index == -1:
                break

            member_start = find_member_start(masked, class_open + 1, brace_index)
            header_masked = masked[member_start:brace_index]
            header_original = source[member_start:brace_index]

            if re.search(r"\b(class|interface|enum|record)\b", header_masked):
                nested_end = find_matching_brace(masked, brace_index)
                cursor = brace_index + 1 if nested_end == -1 else nested_end + 1
                continue

            method_name = extract_method_name(header_masked)
            if not method_name or not looks_like_method_header(header_masked, method_name):
                cursor = brace_index + 1
                continue

            method_end = find_matching_brace(masked, brace_index)
            if method_end == -1 or method_end > class_close:
                cursor = brace_index + 1
                continue

            method_start_line = line_number(line_starts, member_start)
            method_end_line = line_number(line_starts, method_end)
            method_line_count = max(1, method_end_line - method_start_line + 1)
            if method_line_count < min_method_lines:
                cursor = method_end + 1
                continue

            method_tokens = tokenize(masked[brace_index : method_end + 1])
            if not method_tokens:
                cursor = method_end + 1
                continue

            method_signature = " ".join(header_original.replace("\n", " ").split())
            modifiers = extract_modifiers(header_masked)
            normalized = normalize_tokens(method_tokens)
            risk_level, risk_reasons = assess_method_risk(
                method_signature,
                source[brace_index : method_end + 1],
                modifiers,
            )

            methods.append(
                JavaMethodInfo(
                    uid=f"{class_info.file}:{class_info.name}:{method_name}:{method_start_line}",
                    file=class_info.file,
                    package=class_info.package,
                    class_name=class_info.name,
                    method_name=method_name,
                    signature=method_signature,
                    modifiers=modifiers,
                    start_line=method_start_line,
                    end_line=method_end_line,
                    line_count=method_line_count,
                    token_count=len(method_tokens),
                    generalized=generalize_tokens(method_tokens),
                    hash_exact=sha1(normalized),
                    risk_level=risk_level,
                    risk_reasons=risk_reasons,
                )
            )

            cursor = method_end + 1

    return class_infos, methods


def group_exact(items: Sequence[object], hash_attr: str) -> List[List[object]]:
    buckets: Dict[str, List[object]] = defaultdict(list)
    for item in items:
        buckets[getattr(item, hash_attr)].append(item)
    groups = [group for group in buckets.values() if len(group) >= 2]
    groups.sort(key=lambda group: (-len(group), -sum(getattr(item, "line_count", 0) for item in group)))
    return groups


class UnionFind:
    def __init__(self, size: int):
        self.parent = list(range(size))
        self.rank = [0] * size

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, x: int, y: int) -> None:
        root_x = self.find(x)
        root_y = self.find(y)
        if root_x == root_y:
            return
        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
            return
        if self.rank[root_x] > self.rank[root_y]:
            self.parent[root_y] = root_x
            return
        self.parent[root_y] = root_x
        self.rank[root_x] += 1


def group_similar(
    items: Sequence[object],
    threshold: float,
    max_comparisons: int,
) -> Tuple[List[Tuple[List[object], float]], int, bool]:
    if len(items) < 2:
        return [], 0, False

    sorted_items = sorted(items, key=lambda item: getattr(item, "token_count"))
    uf = UnionFind(len(sorted_items))

    comparisons = 0
    truncated = False

    for i, left in enumerate(sorted_items):
        upper_bound = int(getattr(left, "token_count") * 1.25) + 8
        for j in range(i + 1, len(sorted_items)):
            right = sorted_items[j]
            if getattr(right, "token_count") > upper_bound:
                break
            if getattr(left, "hash_exact") == getattr(right, "hash_exact"):
                continue

            comparisons += 1
            if comparisons > max_comparisons:
                truncated = True
                break

            ratio = SequenceMatcher(None, getattr(left, "generalized"), getattr(right, "generalized")).ratio()
            if ratio >= threshold:
                uf.union(i, j)
        if truncated:
            break

    clusters: Dict[int, List[int]] = defaultdict(list)
    for index in range(len(sorted_items)):
        clusters[uf.find(index)].append(index)

    grouped: List[Tuple[List[object], float]] = []
    for cluster_indices in clusters.values():
        if len(cluster_indices) < 2:
            continue
        members = [sorted_items[index] for index in cluster_indices]
        best_ratio = 0.0
        for left_idx in range(len(members)):
            for right_idx in range(left_idx + 1, len(members)):
                ratio = SequenceMatcher(
                    None,
                    getattr(members[left_idx], "generalized"),
                    getattr(members[right_idx], "generalized"),
                ).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
        grouped.append((members, round(best_ratio, 4)))

    grouped.sort(key=lambda pair: (-len(pair[0]), -pair[1]))
    return grouped, comparisons, truncated


def risk_score(level: str) -> int:
    return {"low": 0, "medium": 1, "high": 2}.get(level, 1)


def aggregate_group_risk(methods: Sequence[JavaMethodInfo]) -> Tuple[str, List[str]]:
    level = "low"
    reasons: List[str] = []
    for method in methods:
        if risk_score(method.risk_level) > risk_score(level):
            level = method.risk_level
        reasons.extend(method.risk_reasons)
    return level, unique(reasons)


def common_safety_checks() -> List[str]:
    return [
        "保持 public/protected 方法签名与可见性不变；若必须变更，先提供兼容桥接层。",
        "保留原注解语义（事务、安全、缓存、重试等），避免因迁移位置导致框架行为变化。",
        "先补表征测试（characterization tests）覆盖旧行为，再做去重。",
        "每个重复组单独改动并完成编译 + 受影响测试后再进入下一组。",
        "对比异常类型、日志、副作用调用顺序，确认去重前后完全一致。",
    ]


def recommendation_for_method_group(methods: Sequence[JavaMethodInfo], group_kind: str) -> Dict[str, object]:
    level, reasons = aggregate_group_risk(methods)
    same_class = len({(method.file, method.class_name) for method in methods}) == 1
    all_private = all("private" in method.modifiers for method in methods)
    all_static = all("static" in method.modifiers for method in methods)

    if level == "high":
        strategy = "先不直接合并实现。先补充表征测试，确认副作用边界后再做小步委托式去重。"
        confidence = "low"
    elif same_class and all_private:
        strategy = "保留一个 private 实现为主实现，其余重复 private 方法改为委托后删除。"
        confidence = "high"
    elif same_class:
        strategy = "抽取单一 private helper，保持原 public/protected 方法作为薄封装，避免破坏外部 API。"
        confidence = "high" if group_kind == "exact" else "medium"
    elif all_static and level == "low":
        strategy = "提取到共享 Utility 静态方法，原位置保留短期委托包装并逐步收敛调用点。"
        confidence = "medium"
    else:
        strategy = "优先提取组合式协作类（helper/service），避免强行继承；保留原入口方法做兼容委托。"
        confidence = "medium" if level == "low" else "low"

    return {
        "risk_level": level,
        "risk_reasons": reasons,
        "strategy": strategy,
        "confidence": confidence,
        "required_checks": common_safety_checks(),
    }


def recommendation_for_class_group(classes: Sequence[JavaClassInfo], group_kind: str) -> Dict[str, object]:
    same_package = len({clazz.package for clazz in classes}) == 1
    if group_kind == "exact" and same_package:
        strategy = "保留一个主类，其余类改为薄委托或删除；分阶段迁移调用点并保留兼容入口。"
        confidence = "high"
    elif group_kind == "exact":
        strategy = "抽公共实现到共享组件（抽象基类或组合 helper），各原类仅保留差异化逻辑。"
        confidence = "medium"
    else:
        strategy = "先抽取重复字段与方法到组合 helper，再评估是否需要统一继承层次。"
        confidence = "medium"

    return {
        "risk_level": "medium",
        "risk_reasons": [
            "类级去重通常会影响依赖注入、包可见性与构造过程，需要分阶段迁移。"
        ],
        "strategy": strategy,
        "confidence": confidence,
        "required_checks": common_safety_checks(),
    }


def to_class_member_payload(clazz: JavaClassInfo) -> Dict[str, object]:
    payload = asdict(clazz)
    payload.pop("generalized", None)
    payload.pop("hash_exact", None)
    return payload


def to_method_member_payload(method: JavaMethodInfo) -> Dict[str, object]:
    payload = asdict(method)
    payload.pop("generalized", None)
    payload.pop("hash_exact", None)
    return payload


def build_class_groups(
    classes: Sequence[JavaClassInfo],
    similarity_threshold: float,
    max_comparisons: int,
) -> Tuple[List[Dict[str, object]], List[Dict[str, object]], int, bool]:
    exact_groups = group_exact(classes, "hash_exact")
    exact_payload: List[Dict[str, object]] = []
    exact_member_ids = set()

    for index, group in enumerate(exact_groups, start=1):
        for member in group:
            exact_member_ids.add(member.uid)
        exact_payload.append(
            {
                "group_id": f"class-exact-{index}",
                "kind": "exact",
                "members": [to_class_member_payload(member) for member in group],
                "recommendation": recommendation_for_class_group(group, "exact"),
            }
        )

    similar_candidates = [clazz for clazz in classes if clazz.uid not in exact_member_ids]
    similar_groups, comparisons, truncated = group_similar(
        similar_candidates,
        threshold=similarity_threshold,
        max_comparisons=max_comparisons,
    )

    similar_payload: List[Dict[str, object]] = []
    for index, (group, score) in enumerate(similar_groups, start=1):
        similar_payload.append(
            {
                "group_id": f"class-similar-{index}",
                "kind": "similar",
                "similarity": score,
                "members": [to_class_member_payload(member) for member in group],
                "recommendation": recommendation_for_class_group(group, "similar"),
            }
        )

    return exact_payload, similar_payload, comparisons, truncated


def build_method_groups(
    methods: Sequence[JavaMethodInfo],
    similarity_threshold: float,
    max_comparisons: int,
) -> Tuple[List[Dict[str, object]], List[Dict[str, object]], int, bool]:
    exact_groups = group_exact(methods, "hash_exact")
    exact_payload: List[Dict[str, object]] = []
    exact_member_ids = set()

    for index, group in enumerate(exact_groups, start=1):
        for member in group:
            exact_member_ids.add(member.uid)
        exact_payload.append(
            {
                "group_id": f"method-exact-{index}",
                "kind": "exact",
                "members": [to_method_member_payload(member) for member in group],
                "recommendation": recommendation_for_method_group(group, "exact"),
            }
        )

    similar_candidates = [method for method in methods if method.uid not in exact_member_ids]
    similar_groups, comparisons, truncated = group_similar(
        similar_candidates,
        threshold=similarity_threshold,
        max_comparisons=max_comparisons,
    )

    similar_payload: List[Dict[str, object]] = []
    for index, (group, score) in enumerate(similar_groups, start=1):
        similar_payload.append(
            {
                "group_id": f"method-similar-{index}",
                "kind": "similar",
                "similarity": score,
                "members": [to_method_member_payload(member) for member in group],
                "recommendation": recommendation_for_method_group(group, "similar"),
            }
        )

    return exact_payload, similar_payload, comparisons, truncated


def resolve_cache_path(root: Path, cache_file: str) -> Path:
    cache_path = Path(cache_file)
    if cache_path.is_absolute():
        return cache_path
    return root / cache_path


def build_cache_signature(args: argparse.Namespace) -> Dict[str, object]:
    return {
        "min_class_lines": args.min_class_lines,
        "min_method_lines": args.min_method_lines,
        "include_tests": bool(args.include_tests),
        "ignore_dirs": sorted(set(args.ignore_dir)),
    }


def file_fingerprint(path: Path) -> Dict[str, int]:
    stat = path.stat()
    return {
        "size": int(stat.st_size),
        "mtime_ns": int(stat.st_mtime_ns),
    }


def load_cache(cache_path: Path) -> Dict[str, object]:
    if not cache_path.exists():
        return {}
    try:
        loaded = json.loads(cache_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"[WARN] Failed to read cache {cache_path}: {exc}", file=sys.stderr)
        return {}
    if not isinstance(loaded, dict):
        return {}
    return loaded


def save_cache(cache_path: Path, payload: Dict[str, object]) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    # Use per-process tmp file names to avoid collisions during concurrent runs.
    tmp_path = cache_path.with_name(f"{cache_path.name}.tmp.{os.getpid()}")
    try:
        tmp_path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        tmp_path.replace(cache_path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def collect_group_ids(
    class_exact: Sequence[Dict[str, object]],
    class_similar: Sequence[Dict[str, object]],
    method_exact: Sequence[Dict[str, object]],
    method_similar: Sequence[Dict[str, object]],
) -> Set[str]:
    ids: Set[str] = set()
    for group in list(class_exact) + list(class_similar) + list(method_exact) + list(method_similar):
        group_id = group.get("group_id")
        if isinstance(group_id, str):
            ids.add(group_id)
    return ids


def member_location(member: Dict[str, object], member_type: str) -> str:
    if member_type == "class":
        return f"{member.get('file', '')}:{member.get('name', '')}:{member.get('start_line', '')}"
    return (
        f"{member.get('file', '')}:{member.get('class_name', '')}:"
        f"{member.get('method_name', '')}:{member.get('start_line', '')}"
    )


def summarize_group(
    group: Dict[str, object],
    member_type: str,
    expanded: bool,
) -> Dict[str, object]:
    members = group.get("members", [])
    recommendation = group.get("recommendation", {})
    summary: Dict[str, object] = {
        "group_id": group.get("group_id"),
        "kind": group.get("kind"),
        "member_count": len(members) if isinstance(members, list) else 0,
        "sample_locations": [
            member_location(member, member_type)
            for member in members[:3]
            if isinstance(member, dict)
        ]
        if isinstance(members, list)
        else [],
        "risk_level": recommendation.get("risk_level"),
        "strategy": recommendation.get("strategy"),
        "confidence": recommendation.get("confidence"),
    }
    if "similarity" in group:
        summary["similarity"] = group.get("similarity")

    if expanded:
        summary["members"] = members
        summary["recommendation"] = recommendation
    else:
        summary["expand_hint"] = (
            "使用 --summary-only --group-id "
            f"{group.get('group_id', '<group-id>')} 展开该组详细成员"
        )

    return summary


def summarize_section(
    section: Dict[str, List[Dict[str, object]]],
    member_type: str,
    expanded_group_ids: Set[str],
) -> Dict[str, List[Dict[str, object]]]:
    summarized = {"exact": [], "similar": []}

    for kind in ("exact", "similar"):
        for group in section.get(kind, []):
            group_id = group.get("group_id")
            expanded = isinstance(group_id, str) and group_id in expanded_group_ids
            summarized[kind].append(summarize_group(group, member_type, expanded))

    return summarized


def main() -> int:
    args = parse_args()

    root = Path(args.root).resolve()
    if not root.exists() or not root.is_dir():
        print(f"[ERROR] --root is not a directory: {root}", file=sys.stderr)
        return 1

    java_files = find_java_files(root, args.ignore_dir, args.include_tests)
    classes: List[JavaClassInfo] = []
    methods: List[JavaMethodInfo] = []

    cache_enabled = not args.no_cache
    cache_hits = 0
    cache_misses = 0
    cache_reasons: List[str] = []
    cache_path = resolve_cache_path(root, args.cache_file)
    cache_signature = build_cache_signature(args)
    existing_cache_files: Dict[str, Dict[str, object]] = {}

    if cache_enabled:
        cache_data = load_cache(cache_path)
        if args.refresh_cache:
            cache_reasons.append("refresh_requested")
        elif not cache_data:
            cache_reasons.append("cache_not_found_or_empty")
        else:
            is_compatible = (
                cache_data.get("version") == CACHE_VERSION
                and cache_data.get("root") == str(root)
                and cache_data.get("signature") == cache_signature
            )
            if is_compatible:
                raw_files = cache_data.get("files", {})
                if isinstance(raw_files, dict):
                    existing_cache_files = raw_files
            else:
                cache_reasons.append("cache_incompatible")

    updated_cache_files: Dict[str, Dict[str, object]] = {}

    for java_file in java_files:
        rel = str(java_file.relative_to(root)).replace("\\", "/")
        current_fingerprint = file_fingerprint(java_file)

        file_classes: List[JavaClassInfo] = []
        file_methods: List[JavaMethodInfo] = []

        cached_entry = existing_cache_files.get(rel) if cache_enabled else None
        if (
            cache_enabled
            and isinstance(cached_entry, dict)
            and cached_entry.get("fingerprint") == current_fingerprint
        ):
            raw_classes = cached_entry.get("classes", [])
            raw_methods = cached_entry.get("methods", [])
            try:
                file_classes = [dataclass_from_dict(JavaClassInfo, item) for item in raw_classes]
                file_methods = [dataclass_from_dict(JavaMethodInfo, item) for item in raw_methods]
                cache_hits += 1
            except TypeError:
                file_classes, file_methods = extract_classes_and_methods(
                    root,
                    java_file,
                    min_class_lines=args.min_class_lines,
                    min_method_lines=args.min_method_lines,
                )
                cache_misses += 1
        else:
            file_classes, file_methods = extract_classes_and_methods(
                root,
                java_file,
                min_class_lines=args.min_class_lines,
                min_method_lines=args.min_method_lines,
            )
            if cache_enabled:
                cache_misses += 1

        if cache_enabled:
            updated_cache_files[rel] = {
                "fingerprint": current_fingerprint,
                "classes": [asdict(item) for item in file_classes],
                "methods": [asdict(item) for item in file_methods],
            }

        classes.extend(item for item in file_classes if item.token_count >= args.min_class_tokens)
        methods.extend(item for item in file_methods if item.token_count >= args.min_method_tokens)

    if cache_enabled:
        cache_payload = {
            "version": CACHE_VERSION,
            "root": str(root),
            "signature": cache_signature,
            "files": updated_cache_files,
        }
        try:
            save_cache(cache_path, cache_payload)
        except OSError as exc:
            cache_reasons.append(f"cache_write_failed:{exc}")

    class_exact, class_similar, class_comparisons, class_truncated = build_class_groups(
        classes,
        similarity_threshold=args.similarity_threshold,
        max_comparisons=args.max_comparisons,
    )
    method_exact, method_similar, method_comparisons, method_truncated = build_method_groups(
        methods,
        similarity_threshold=args.similarity_threshold,
        max_comparisons=args.max_comparisons,
    )

    all_group_ids = collect_group_ids(class_exact, class_similar, method_exact, method_similar)
    requested_group_ids = set(args.group_id)
    expanded_group_ids = requested_group_ids & all_group_ids
    unmatched_group_ids = requested_group_ids - all_group_ids

    duplicate_classes = {
        "exact": class_exact,
        "similar": class_similar,
    }
    duplicate_methods = {
        "exact": method_exact,
        "similar": method_similar,
    }

    if args.summary_only:
        duplicate_classes = summarize_section(duplicate_classes, "class", expanded_group_ids)
        duplicate_methods = summarize_section(duplicate_methods, "method", expanded_group_ids)

    report = {
        "summary": {
            "root": str(root),
            "java_files_scanned": len(java_files),
            "classes_analyzed": len(classes),
            "methods_analyzed": len(methods),
            "duplicate_class_groups": len(class_exact) + len(class_similar),
            "duplicate_method_groups": len(method_exact) + len(method_similar),
            "class_similarity_comparisons": class_comparisons,
            "method_similarity_comparisons": method_comparisons,
            "class_similarity_truncated": class_truncated,
            "method_similarity_truncated": method_truncated,
            "output_mode": "summary" if args.summary_only else "full",
            "safety_policy": "建议优先，不自动改代码；必须通过强制校验后再落地去重",
            "cache_enabled": cache_enabled,
            "cache_path": str(cache_path) if cache_enabled else "",
            "cache_hits": cache_hits if cache_enabled else 0,
            "cache_misses": cache_misses if cache_enabled else 0,
            "cache_notes": cache_reasons,
        },
        "duplicate_classes": duplicate_classes,
        "duplicate_methods": duplicate_methods,
        "safety_principles": [
            "先做识别与分级，再做小步去重；避免跨多个重复组一次性大改。",
            "高风险组（事务/并发/外部副作用）默认不直接合并实现，先补测试与隔离层。",
            "优先保持原 API 与异常语义不变，通过委托桥接逐步迁移。",
        ],
        "limitations": [
            "这是静态近似分析，不等价于编译器语义分析；复杂泛型、宏式代码风格可能产生漏报或误报。",
            "相似度分组基于 token 归一化，建议人工复核每个建议后再执行代码修改。",
        ],
    }

    if requested_group_ids:
        report["summary"]["requested_group_ids"] = sorted(requested_group_ids)
    if expanded_group_ids:
        report["summary"]["expanded_group_ids"] = sorted(expanded_group_ids)
    if unmatched_group_ids:
        report["summary"]["unmatched_group_ids"] = sorted(unmatched_group_ids)
    if args.summary_only:
        report["summary"]["expand_usage"] = "使用 --summary-only --group-id <group_id> 展开具体重复组详情"

    output_text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output_text, encoding="utf-8")
        print(f"[OK] Report written to: {output_path}", file=sys.stderr)

    print(output_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
