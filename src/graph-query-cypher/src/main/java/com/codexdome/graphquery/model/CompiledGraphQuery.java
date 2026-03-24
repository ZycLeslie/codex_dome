package com.codexdome.graphquery.model;

import java.util.List;
import java.util.Map;

/**
 * Validated, generator-ready query model.
 *
 * @param nodes node definitions keyed by alias
 * @param edges edge definitions keyed by alias
 * @param paths compiled path walks with resolved node ordering
 * @param returnItems normalized return items
 * @param limit optional result limit
 */
public record CompiledGraphQuery(Map<String, NodeSpec> nodes,
                                 Map<String, EdgeSpec> edges,
                                 List<CompiledPath> paths,
                                 List<CompiledReturnItem> returnItems,
                                 Integer limit) {
    public CompiledGraphQuery {
        nodes = ModelCopies.immutableMap(nodes);
        edges = ModelCopies.immutableMap(edges);
        paths = ModelCopies.immutableList(paths);
        returnItems = ModelCopies.immutableList(returnItems);
    }
}
