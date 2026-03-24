package com.codexdome.graphquery.model;

/**
 * YAML return item definition.
 *
 * @param kind referenced object kind
 * @param ref alias of the referenced path, node, or edge
 * @param alias output column alias
 */
public record ReturnItemSpec(ReturnItemKind kind, String ref, String alias) {
}
