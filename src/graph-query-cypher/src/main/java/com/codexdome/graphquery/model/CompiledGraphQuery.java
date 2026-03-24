package com.codexdome.graphquery.model;

import java.util.List;
import java.util.Map;

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
