package com.codexdome.graphquery.model;

public enum ReturnItemKind {
    PATH,
    NODE,
    EDGE;

    public static ReturnItemKind fromString(String value) {
        if (value == null || value.trim().isEmpty()) {
            return null;
        }
        return ReturnItemKind.valueOf(value.trim().toUpperCase());
    }
}
