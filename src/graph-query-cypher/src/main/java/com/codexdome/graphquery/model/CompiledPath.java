package com.codexdome.graphquery.model;

import java.util.List;

/**
 * Path model with both edge aliases and the fully reconstructed node walk.
 *
 * @param alias path alias used in MATCH and RETURN
 * @param nodeAliases ordered node aliases derived from the path edges
 * @param edgeAliases ordered edge aliases declared by the path
 */
public record CompiledPath(String alias, List<String> nodeAliases, List<String> edgeAliases) {
    public CompiledPath {
        nodeAliases = ModelCopies.immutableList(nodeAliases);
        edgeAliases = ModelCopies.immutableList(edgeAliases);
    }
}
