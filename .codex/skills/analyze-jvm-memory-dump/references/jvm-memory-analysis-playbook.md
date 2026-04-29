# JVM Memory Analysis Playbook

## Artifact roles

- HPROF heap dump: primary evidence for retained heap, dominator tree, leak suspects, path-to-GC-roots, duplicate strings, classloader retention, and thread local ownership.
- Native/core dump: primary evidence when the JVM or container produced an OS-level core. Use `jhsdb`, `gdb`, or vendor tooling with the matching JDK/JVM build before drawing heap conclusions.
- Class histogram text: output from `jmap -histo`, `jcmd <pid> GC.class_histogram`, MAT histogram exports, or comparable files with any filename. Use for shallow heap ranking and quick class pressure signals. It does not show ownership or retained heap.
- Javacore/thread dump text: HotSpot thread dumps, OpenJ9/IBM javacores, or comparable diagnostic text files with any filename. Use for dump reason, OOM subtype, JVM flags, heap/native memory sections, and thread states.
- Docker/system snapshots: cgroup memory, `ps`, `top`, `jstat`, `lsof`, `netstat`, and `df` outputs explain limits, native pressure, threads, file descriptors, sockets, and capture completeness around the dump.
- GC logs and platform events: use to prove timing, pressure trend, OOMKill, heap sizing, promotion failure, allocation rate, and whether the process was killed outside the JVM.

## HPROF commands

Prefer Eclipse MAT for offline HPROF analysis:

```bash
ParseHeapDump.sh dump.hprof org.eclipse.mat.api:suspects org.eclipse.mat.api:overview org.eclipse.mat.api:top_components
```

Use enough MAT heap to parse the dump, often several GB for large dumps:

```bash
ParseHeapDump.sh dump.hprof org.eclipse.mat.api:suspects -vmargs -Xmx8g
```

Useful MAT views:

- Leak Suspects: first pass for retained heap owners.
- Dominator Tree: sort by retained heap and inspect owners.
- Histogram: compare shallow bytes with `histo.txt`.
- Path to GC Roots: identify static fields, thread locals, classloaders, JNI roots, or finalizer queues.
- Class Loader Explorer: diagnose redeploy/classloader leaks.
- Duplicate Strings: identify excessive repeated text.

When MAT is not available, capture metadata only and request a MAT/VisualVM/JProfiler text export. Raw `strings` scans can find clues but cannot prove retention.

## Native/core dump commands

Use a matching JDK/JVM binary whenever possible:

```bash
jhsdb jmap --binaryheap --dumpfile heap-from-core.hprof --exe <path-to-java> --core core.dump
jhsdb jstack --exe <path-to-java> --core core.dump
gdb <path-to-java> core.dump
```

If `jhsdb` can extract an HPROF from the core, analyze that HPROF with MAT. If it cannot, keep conclusions limited to native/core evidence and auxiliary snapshots.

## Auxiliary Docker/system evidence

Use these files to support or challenge what the dump says:

- cgroup/container memory: proves container limit, usage, RSS/cache split, memory fail counters, and OOM state. High cgroup usage with modest Java heap points toward native/off-heap/thread/metaspace/container pressure.
- `ps aux` and `ps efwww`: show PID, RSS/VSZ, Java command line, JVM flags, agents, `-Xmx`, `-Xss`, metaspace, direct memory, and GC options.
- `ps -fLf`: shows LWP/thread count by PID. High thread count is strong support for native-thread OOM and stack memory pressure.
- `top -b -H -d2 -n3`: shows near-capture CPU/RSS and hot Java threads/processes.
- `jstat -gcutil`: shows heap generation, metaspace, compressed class space, young/full GC counts, and whether the JVM was under GC pressure.
- `lsof -p`: shows file descriptor count, socket count, deleted open files, mapped files, JARs, and other native resources.
- `netstat -nap` or aggregated netstat: shows connection states. Many `CLOSE_WAIT` can indicate leaked sockets; huge `ESTABLISHED`/`TIME_WAIT` can explain buffers and thread pressure.
- `df -h`: explains dump/log truncation or failure to write heap dumps when the filesystem is full.

Do not let auxiliary evidence override retained-heap evidence by itself. Use it to classify the memory problem and explain why a dump may not match RSS or container kill behavior.

## Histogram interpretation

Treat rows as shallow heap:

- `[B` / `byte[]`: payloads, buffers, serialized data, compressed content, images, network bodies, caches, or direct-buffer wrappers.
- `[C`, `java.lang.String`, `[Ljava.lang.Object;`: text volume, duplicate strings, JSON/XML payloads, large collections, or result-set materialization.
- `java.util.HashMap$Node`, `ConcurrentHashMap$Node`, `LinkedHashMap$Entry`: map/caching pressure. Find the owning map in HPROF dominator paths.
- `java.lang.Class`, reflection metadata, generated proxy classes, classloader classes: possible classloader/metaspace leak, dynamic code generation, or excessive reflection caches.
- `java.nio.DirectByteBuffer`, `MappedByteBuffer`: off-heap pressure may exceed Java heap. Check `MaxDirectMemorySize`, native memory, and container limits.
- `java.lang.Thread`, `ThreadLocal$ThreadLocalMap$Entry`: possible thread or ThreadLocal leak. Check javacore thread counts and HPROF GC roots.

Strong evidence comes from:

- the same class growing across multiple histograms;
- MAT retained heap pointing to the same owner;
- allocation stack traces, application logs, or code paths matching the suspect class/package;
- memory drops after clearing a cache, queue, session, or pool in a controlled test.

## Javacore and OOM signatures

Look for dump trigger and OOM subtype:

- `java/lang/OutOfMemoryError`, `java.lang.OutOfMemoryError`: Java-side OOM.
- `Java heap space`: heap exhaustion.
- `GC overhead limit exceeded`: excessive GC with little recovery; still identify the retained owner.
- `Metaspace` or `Compressed class space`: class metadata/classloader pressure.
- `Direct buffer memory`: off-heap direct buffer pressure.
- `unable to create new native thread`: native memory, process limits, thread leak, or stack sizing.
- Container `OOMKilled`: external kill; JVM may not emit a Java OOM.

Inspect JVM flags:

- `-Xmx`, `-Xms`, `-Xmn`, `-Xss`
- `-XX:MaxMetaspaceSize`
- `-XX:MaxDirectMemorySize`
- GC collector and region sizing flags
- `-XX:+HeapDumpOnOutOfMemoryError`
- container support flags and cgroup limits

Thread states matter when memory is tied to concurrency:

- high thread count plus native-thread OOM suggests thread leak or overly large pools;
- many blocked threads can retain large request/session objects while waiting;
- thread locals retain objects through thread GC roots even after request completion.

## Diagnosis patterns

- Cache leak: retained owner is a cache/map, entries grow without eviction, keys or values are application domain objects.
- Queue backlog: retained owner is a queue/ring buffer/executor/workflow engine, with many pending tasks or messages.
- Request/session retention: web/session/request objects dominate, often through thread locals, async contexts, or long-lived maps.
- Classloader leak: old application classloaders retained by static fields, threads, JDBC drivers, logging frameworks, MBeans, or ThreadLocals.
- Direct-buffer pressure: Java heap looks acceptable, but direct buffer classes/native memory/container RSS are high.
- Thread leak: javacore shows excessive threads; HPROF roots show thread stacks or ThreadLocals retaining payloads.
- Large result materialization: arrays, strings, ORM entities, or JSON trees dominate after batch queries or exports.

## Report confidence

- High: HPROF retained heap plus path-to-GC-roots plus matching code owner.
- Medium: repeated histogram growth plus matching logs/code/package names.
- Low: single histogram or javacore clue without owner or trend.
- Inconclusive: only metadata, truncated files, no incident timestamp, or only post-kill platform events.
