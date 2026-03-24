package com.codexdome.graphquery.model;

import java.util.List;

public record CompiledPath(String alias, List<String> nodeAliases, List<String> edgeAliases) {
    public CompiledPath {
        nodeAliases = ModelCopies.immutableList(nodeAliases);
        edgeAliases = ModelCopies.immutableList(edgeAliases);
    }
}
