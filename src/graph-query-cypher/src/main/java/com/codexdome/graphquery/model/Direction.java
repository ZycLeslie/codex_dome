package com.codexdome.graphquery.model;

/**
 * Supported relationship directions in the YAML schema.
 */
public enum Direction {
    OUTBOUND,
    INBOUND,
    UNDIRECTED;

    /**
     * Parses a direction value in a case-insensitive way.
     *
     * @param value raw YAML value
     * @return parsed direction, or {@code null} when the input is blank
     */
    public static Direction fromString(String value) {
        if (value == null || value.trim().isEmpty()) {
            return null;
        }
        return Direction.valueOf(value.trim().toUpperCase());
    }
}
