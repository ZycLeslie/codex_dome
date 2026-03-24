package com.codexdome.graphquery.model;

import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Utility methods that defensively copy collection-based model fields into immutable views.
 */
public final class ModelCopies {
    private ModelCopies() {
    }

    /**
     * Returns an immutable copy of the supplied list.
     *
     * @param source source list, possibly {@code null}
     * @param <T> element type
     * @return immutable list copy
     */
    public static <T> List<T> immutableList(List<T> source) {
        if (source == null) {
            return Collections.emptyList();
        }
        return Collections.unmodifiableList(new ArrayList<T>(source));
    }

    /**
     * Returns an immutable insertion-ordered copy of the supplied map.
     *
     * @param source source map, possibly {@code null}
     * @param <K> key type
     * @param <V> value type
     * @return immutable map copy
     */
    public static <K, V> Map<K, V> immutableMap(Map<K, V> source) {
        if (source == null) {
            return Collections.emptyMap();
        }
        return Collections.unmodifiableMap(new LinkedHashMap<K, V>(source));
    }
}
