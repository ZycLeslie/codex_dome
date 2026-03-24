package com.codexdome.graphquery.model;

import java.util.List;

public record ReturnSpec(List<ReturnItemSpec> items) {
    public ReturnSpec {
        items = ModelCopies.immutableList(items);
    }

    public static ReturnSpec empty() {
        return new ReturnSpec(java.util.Collections.<ReturnItemSpec>emptyList());
    }
}
