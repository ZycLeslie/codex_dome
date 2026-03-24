package com.codexdome.graphquery.validation;

/**
 * Single validation error entry with its field path and human-readable message.
 *
 * @param field field path that failed validation
 * @param message validation message
 */
public record ValidationError(String field, String message) {
}
