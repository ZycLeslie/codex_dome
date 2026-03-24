package com.codexdome.graphquery.model;

import java.util.List;
import java.util.Map;

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
