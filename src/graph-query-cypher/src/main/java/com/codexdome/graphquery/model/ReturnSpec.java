package com.codexdome.graphquery.model;

import java.util.List;

/**
 * Return section of the YAML document.
 *
 * @param items explicit return items; an empty list means "return every named path"
 */
public record ReturnSpec(List<ReturnItemSpec> items) {
    public ReturnSpec {
        items = ModelCopies.immutableList(items);
    }

    /**
     * Returns an empty return specification that triggers the default path-return behavior.
     *
     * @return empty return specification
     */
    public static ReturnSpec empty() {
        return new ReturnSpec(java.util.Collections.<ReturnItemSpec>emptyList());
    }
}
