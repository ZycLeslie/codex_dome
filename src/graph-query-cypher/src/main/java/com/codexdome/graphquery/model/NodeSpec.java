package com.codexdome.graphquery.model;

import java.util.List;
import java.util.Map;

public record NodeSpec(List<String> labels, Object id, Map<String, Object> properties) {
    public NodeSpec {
        labels = ModelCopies.immutableList(labels);
        properties = ModelCopies.immutableMap(properties);
    }
}
