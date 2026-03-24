package com.codexdome.graphquery.model;

import java.util.List;

public record PathSpec(String alias, List<String> edges) {
    public PathSpec {
        edges = ModelCopies.immutableList(edges);
    }
}
