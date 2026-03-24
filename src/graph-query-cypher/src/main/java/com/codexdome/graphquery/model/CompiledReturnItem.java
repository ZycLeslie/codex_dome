package com.codexdome.graphquery.model;

/**
 * Normalized return item consumed by the Cypher generator.
 *
 * @param kind referenced object kind
 * @param ref alias of the referenced path, node, or edge
 * @param alias output column alias
 */
public record CompiledReturnItem(ReturnItemKind kind, String ref, String alias) {
}
