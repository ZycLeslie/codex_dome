package com.codexdome.graphquery.model;

import java.util.Map;

/**
 * YAML edge definition.
 *
 * @param from source node alias
 * @param to target node alias
 * @param direction direction to render in Cypher
 * @param type optional relationship type
 * @param id optional business id filter rendered as {@code alias.id = $param}
 * @param properties additional edge property filters
 */
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
