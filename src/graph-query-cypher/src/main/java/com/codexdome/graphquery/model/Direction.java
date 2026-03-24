package com.codexdome.graphquery.model;

public enum Direction {
    OUTBOUND,
    INBOUND,
    UNDIRECTED;

    public static Direction fromString(String value) {
        if (value == null || value.trim().isEmpty()) {
            return null;
        }
        return Direction.valueOf(value.trim().toUpperCase());
    }
}
