package com.codexdome.graphquery;

import com.codexdome.graphquery.model.ModelCopies;

import java.util.Map;

/**
 * Immutable result of Cypher generation.
 *
 * @param query generated Cypher statement
 * @param params parameter map referenced by the statement
 */
public record GeneratedCypherQuery(String query, Map<String, Object> params) {
    public GeneratedCypherQuery {
        if (query == null || query.trim().isEmpty()) {
            throw new IllegalArgumentException("query must not be empty");
        }
        params = ModelCopies.immutableMap(params);
    }
}
