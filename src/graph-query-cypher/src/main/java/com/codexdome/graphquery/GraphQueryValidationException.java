package com.codexdome.graphquery;

import com.codexdome.graphquery.validation.ValidationError;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Exception raised when a parsed document violates the graph-query schema or semantic rules.
 */
public final class GraphQueryValidationException extends GraphQueryException {
    private final List<ValidationError> errors;

    /**
     * Creates a validation exception that retains every discovered error.
     *
     * @param errors validation errors collected during compilation
     */
    public GraphQueryValidationException(List<ValidationError> errors) {
        super(buildMessage(errors));
        this.errors = Collections.unmodifiableList(new ArrayList<ValidationError>(errors));
    }

    /**
     * Returns the immutable list of validation errors that caused the failure.
     *
     * @return collected validation errors
     */
    public List<ValidationError> errors() {
        return errors;
    }

    private static String buildMessage(List<ValidationError> errors) {
        StringBuilder builder = new StringBuilder("Graph query validation failed");
        for (ValidationError error : errors) {
            builder.append("\n - ").append(error.field()).append(": ").append(error.message());
        }
        return builder.toString();
    }
}
