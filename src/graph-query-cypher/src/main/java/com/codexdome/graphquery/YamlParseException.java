package com.codexdome.graphquery;

/**
 * Exception raised when YAML cannot be parsed into the supported graph-query subset.
 */
public final class YamlParseException extends GraphQueryException {
    /**
     * Creates an exception with a message only.
     *
     * @param message error description
     */
    public YamlParseException(String message) {
        super(message);
    }

    /**
     * Creates an exception with both message and cause.
     *
     * @param message error description
     * @param cause root cause
     */
    public YamlParseException(String message, Throwable cause) {
        super(message, cause);
    }
}
