package com.codexdome.graphquery.model;

/**
 * Supported return item kinds.
 */
public enum ReturnItemKind {
    PATH,
    NODE,
    EDGE;

    /**
     * Parses a return item kind in a case-insensitive way.
     *
     * @param value raw YAML value
     * @return parsed kind, or {@code null} when the input is blank
     */
    public static ReturnItemKind fromString(String value) {
        if (value == null || value.trim().isEmpty()) {
            return null;
        }
        return ReturnItemKind.valueOf(value.trim().toUpperCase());
    }
}
