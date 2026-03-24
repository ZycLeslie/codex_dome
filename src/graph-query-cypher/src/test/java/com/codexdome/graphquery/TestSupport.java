package com.codexdome.graphquery;

import java.util.Map;

final class TestSupport {
    private TestSupport() {
    }

    static void assertEquals(Object expected, Object actual, String message) {
        if (expected == null ? actual != null : !expected.equals(actual)) {
            throw new AssertionError(message + "\nExpected: " + expected + "\nActual:   " + actual);
        }
    }

    static void assertTrue(boolean condition, String message) {
        if (!condition) {
            throw new AssertionError(message);
        }
    }

    static void assertContains(String actual, String expectedFragment, String message) {
        if (actual == null || !actual.contains(expectedFragment)) {
            throw new AssertionError(message + "\nMissing fragment: " + expectedFragment + "\nActual: " + actual);
        }
    }

    static void assertMapContains(Map<String, Object> params, String key, Object expectedValue) {
        assertTrue(params.containsKey(key), "Expected params to contain key '" + key + "'");
        assertEquals(expectedValue, params.get(key), "Unexpected value for param '" + key + "'");
    }

    static void fail(String message) {
        throw new AssertionError(message);
    }
}
