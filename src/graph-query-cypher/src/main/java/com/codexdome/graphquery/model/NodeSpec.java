package com.codexdome.graphquery.model;

import java.util.List;
import java.util.Map;

/**
 * YAML node definition.
 *
 * @param labels optional node labels rendered into the node pattern
 * @param id optional business id filter rendered as {@code alias.id = $param}
 * @param properties additional node property filters
 */
public record NodeSpec(List<String> labels, Object id, Map<String, Object> properties) {
    public NodeSpec {
        labels = ModelCopies.immutableList(labels);
        properties = ModelCopies.immutableMap(properties);
    }
}
