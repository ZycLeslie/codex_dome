package com.codexdome.graphquery.model;

import java.util.Map;

public record EdgeSpec(String from,
                       String to,
                       Direction direction,
                       String type,
                       Object id,
                       Map<String, Object> properties) {
    public EdgeSpec {
        properties = ModelCopies.immutableMap(properties);
    }
}
