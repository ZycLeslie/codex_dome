package com.codexdome.graphquery;

public class GraphQueryException extends RuntimeException {
    public GraphQueryException(String message) {
        super(message);
    }

    public GraphQueryException(String message, Throwable cause) {
        super(message, cause);
    }
}
