package com.codexdome.graphquery.model;

import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public final class ModelCopies {
    private ModelCopies() {
    }

    public static <T> List<T> immutableList(List<T> source) {
        if (source == null) {
            return Collections.emptyList();
        }
        return Collections.unmodifiableList(new ArrayList<T>(source));
    }

    public static <K, V> Map<K, V> immutableMap(Map<K, V> source) {
        if (source == null) {
            return Collections.emptyMap();
        }
        return Collections.unmodifiableMap(new LinkedHashMap<K, V>(source));
    }
}
