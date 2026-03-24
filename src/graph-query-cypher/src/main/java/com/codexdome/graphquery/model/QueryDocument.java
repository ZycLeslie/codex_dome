package com.codexdome.graphquery.model;

/**
 * Top-level YAML document.
 *
 * @param version schema version
 * @param query query definition payload
 */
public record QueryDocument(int version, QuerySpec query) {
}
