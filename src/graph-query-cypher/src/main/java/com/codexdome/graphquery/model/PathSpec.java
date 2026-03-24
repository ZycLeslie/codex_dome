package com.codexdome.graphquery.model;

import java.util.List;

/**
 * YAML path definition expressed as an ordered list of edge aliases.
 *
 * @param alias path alias used in MATCH and RETURN
 * @param edges ordered edge aliases that must form a continuous chain
 */
public record PathSpec(String alias, List<String> edges) {
    public PathSpec {
        edges = ModelCopies.immutableList(edges);
    }
}
