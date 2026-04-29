---
name: analyze-jvm-memory-dump
description: Directly analyze JVM dump packages, with the heap/native dump as primary evidence and class histograms, javacores/thread dumps, Docker/cgroup memory snapshots, jstat, lsof, netstat, ps, top, df, GC logs, and application logs as auxiliary evidence regardless of filename. Use when Codex needs to diagnose Java memory leaks, OutOfMemoryError, heap/native/metaspace/direct-buffer pressure, suspicious retained objects, classloader leaks, container OOMKill, or memory coredump/堆转储/内存 dump artifacts.
---

# Analyze JVM Memory Dump

## Overview

Use this skill to turn a JVM dump package into an evidence-backed leak or memory-pressure diagnosis. Start from the dump itself, then use text artifacts and Docker/system snapshots only to explain the runtime boundary conditions around the dump.

## Quick Start

1. Locate the primary dump first. It is usually `.hprof` or a file whose header starts with `JAVA PROFILE`, but may also be a native/core dump (`core`, `.dmp`, `.dump`) that needs `jhsdb`, `gdb`, or vendor tooling.

2. Run direct dump analysis:

   ```bash
   python3 <skill-dir>/scripts/analyze_heap_dump.py <dump-file> --out-dir /tmp/jvm-dump-analysis --mat-xmx 8g
   ```

   This script runs Eclipse MAT headless reports when `ParseHeapDump.sh` is available. If MAT is not installed, it records dump metadata and prints exact commands to run. For native/core dumps, it prints `jhsdb`/`gdb` next steps instead of pretending to parse retained heap.

3. Run the package summarizer on the surrounding directory:

   ```bash
   python3 <skill-dir>/scripts/summarize_memory_artifacts.py <artifact-or-dir> --format markdown --out /tmp/jvm-memory-summary.md
   ```

   Use `--format json` when another tool or spreadsheet will consume the output. The script content-detects class histograms, javacores/thread dumps, HPROF/core dump metadata, and auxiliary Docker/system command outputs. Filename hints such as `docker_` prefixes are useful but not required.

   If a file has an arbitrary name or unusual format, force the type explicitly:

   ```bash
   python3 <skill-dir>/scripts/summarize_memory_artifacts.py <file> --type histogram
   python3 <skill-dir>/scripts/summarize_memory_artifacts.py <file> --type javacore
   python3 <skill-dir>/scripts/summarize_memory_artifacts.py <file> --type cgroup_memory
   ```

4. Cross-check direct dump findings with auxiliary evidence before making recommendations. The dump identifies retained owners; auxiliary files explain whether the incident was heap, native/off-heap, thread, file descriptor, container limit, disk, or network related.

## Workflow

### 1. Directly analyze the dump

- For HPROF, prefer MAT headless reports (`suspects`, `overview`, `top_components`) or an equivalent trusted heap analyzer.
- Inspect leak suspects, dominator tree, retained heap, classloader explorer, duplicate strings, thread locals, finalizer queues, and path-to-GC-roots.
- For native/core dumps, use the matching JDK/JVM build with `jhsdb` or vendor tooling to derive heap/thread evidence when possible.
- Do not load multi-GB dump files into context. Work from tool-generated text reports and small metadata summaries.

### 2. Inventory auxiliary evidence

Use `scripts/summarize_memory_artifacts.py` on the directory. Treat these as supporting evidence:

- cgroup/container memory (`cgroup-memory*.out`, memory.stat, docker-prefixed variants): container limit, usage, RSS/cache split, failcnt, OOM counters.
- `ps aux` / `ps efwww`: Java command line, JVM flags, PID, RSS/VSZ, agents, `-Xmx`, direct memory, metaspace, GC options.
- `ps -fLf`: native thread/LWP count; essential for "unable to create native thread" and stack memory pressure.
- `top -b -H ...`: process/thread CPU and RSS snapshot near capture time.
- `jstat -gcutil`: heap generation/metaspace occupancy and full-GC pressure around the dump.
- `lsof -p`: file descriptor/socket counts, deleted open files, mapped files, and native resource pressure.
- `netstat -nap` / aggregated netstat: CLOSE_WAIT, ESTABLISHED, TIME_WAIT, listen sockets that may explain retained buffers, blocked threads, or connection-pool pressure.
- `df -h`: disk pressure that can truncate dumps/logs or prevent heap dump creation.
- class histograms and javacores/thread dumps: shallow heap ranking, OOM subtype, thread states, JVM flags, and memory section details.

### 3. Correlate dump and snapshots

- Match timestamps across dump, javacore/thread dump, histogram, GC log, application log, deployment event, cgroup sample, and container OOMKill event.
- Separate retained heap evidence from auxiliary evidence. The dump can prove ownership; histograms, ps, top, and cgroup files provide context.
- Distinguish Java heap pressure from off-heap/native pressure: direct buffers, mapped buffers, JNI, thread stacks, metaspace, code cache, malloc arenas, and container accounting.
- Tie suspected owners to class/package names, MAT paths, thread names, caches, connection pools, queues, ORM/session objects, buffers, classloaders, or native resources.

### 4. Deliver the diagnosis

Return a concise report with:

1. Scope: primary dump analyzed, auxiliary files present/missing, timestamps, JVM/vendor, and whether retained-heap/core analysis succeeded.
2. Incident type: heap leak, normal high heap occupancy, native/off-heap pressure, metaspace/classloader leak, thread leak, or inconclusive.
3. Top evidence table: suspect, metric, artifact, exact marker, confidence.
4. Root-cause hypothesis: likely owner, why it retains memory, and what evidence is missing.
5. Recommended actions: code/config fixes, validation commands, and next capture plan.
6. Gaps: missing HPROF report, missing GC logs, single snapshot only, clock skew, truncated files, or post-OOM bias.

## Reference

Read `references/jvm-memory-analysis-playbook.md` when you need interpretation rules, common leak signatures, or tool commands for HPROF, histograms, javacores, and native-memory cases.

## Guardrails

- Do not demote the dump behind `histo` or `javacore`; those are auxiliary unless they contain the only available OOM subtype or thread evidence.
- Do not claim a memory leak from a single histogram without retained-heap, growth-over-time, or owner-path evidence.
- Do not use online heap dump analyzers for sensitive production dumps unless the user explicitly approves the data handling risk.
- Do not echo secrets, tokens, request bodies, or personal data found in heap strings; summarize and redact.
- Do not conflate Java heap OOM with container OOMKill, direct-buffer OOM, metaspace OOM, or native-thread OOM.
- Prefer absolute numbers and percentages. State whether each conclusion is exact, inferred, or speculative.
