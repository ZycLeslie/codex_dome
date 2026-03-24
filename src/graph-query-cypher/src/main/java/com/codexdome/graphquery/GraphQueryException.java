package com.codexdome.graphquery;

/**
 * Base runtime exception for the graph-query compiler module.
 */
public class GraphQueryException extends RuntimeException {
    /**
     * Creates an exception with a message only.
     *
     * @param message error description
     */
    public GraphQueryException(String message) {
        super(message);
    }

    /**
     * Creates an exception with both message and cause.
     *
     * @param message error description
     * @param cause root cause
     */
    public GraphQueryException(String message, Throwable cause) {
        super(message, cause);
    }
}
