package com.codexdome.graphquery.model;

import java.util.List;
import java.util.Map;

/**
 * Root query payload declared under {@code query:}.
 *
 * @param nodes node definitions keyed by alias
 * @param edges edge definitions keyed by alias
 * @param paths named paths built from edge aliases
 * @param returnSpec explicit return items, or empty for the default path return behavior
 * @param limit optional result limit
 */
public record QuerySpec(Map<String, NodeSpec> nodes,
                        Map<String, EdgeSpec> edges,
                        List<PathSpec> paths,
                        ReturnSpec returnSpec,
                        Integer limit) {
    public QuerySpec {
        nodes = ModelCopies.immutableMap(nodes);
        edges = ModelCopies.immutableMap(edges);
        paths = ModelCopies.immutableList(paths);
        returnSpec = returnSpec == null ? ReturnSpec.empty() : returnSpec;
    }
}
