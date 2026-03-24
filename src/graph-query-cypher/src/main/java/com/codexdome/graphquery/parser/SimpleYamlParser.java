package com.codexdome.graphquery.parser;

import com.codexdome.graphquery.YamlParseException;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public final class SimpleYamlParser {
    private List<Line> lines;
    private int index;

    public Object parse(String yaml) {
        if (yaml == null) {
            throw new YamlParseException("YAML input must not be null");
        }
        this.lines = preprocess(yaml);
        this.index = 0;
        if (lines.isEmpty()) {
            return new LinkedHashMap<String, Object>();
        }

        Object value = parseBlock(lines.get(0).indent());
        if (index < lines.size()) {
            Line line = lines.get(index);
            throw error(line, "Unexpected trailing content");
        }
        return value;
    }

    private Object parseBlock(int indent) {
        Line line = current();
        if (line.indent() != indent) {
            throw error(line, "Unexpected indentation: expected " + indent + " spaces but found " + line.indent());
        }
        if (isSequenceLine(line, indent)) {
            return parseSequence(indent);
        }
        return parseMapping(indent, new LinkedHashMap<String, Object>());
    }

    private Map<String, Object> parseMapping(int indent, Map<String, Object> target) {
        while (hasCurrent()) {
            Line line = current();
            if (line.indent() < indent) {
                break;
            }
            if (line.indent() > indent) {
                throw error(line, "Unexpected indentation inside mapping");
            }
            if (isSequenceLine(line, indent)) {
                throw error(line, "Unexpected sequence item inside mapping");
            }

            advance();
            KeyValue keyValue = parseKeyValue(line.content(), line.number());
            if (target.containsKey(keyValue.key())) {
                throw error(line, "Duplicate key '" + keyValue.key() + "'");
            }
            target.put(keyValue.key(), resolveValue(keyValue.valueText(), indent));
        }
        return target;
    }

    private List<Object> parseSequence(int indent) {
        List<Object> items = new ArrayList<Object>();
        while (hasCurrent()) {
            Line line = current();
            if (line.indent() < indent) {
                break;
            }
            if (line.indent() > indent) {
                throw error(line, "Unexpected indentation inside sequence");
            }
            if (!isSequenceLine(line, indent)) {
                throw error(line, "Expected a sequence item");
            }

            advance();
            String itemBody = sequenceItemBody(line.content());
            if (itemBody.isEmpty()) {
                if (!hasNestedBlock(indent)) {
                    throw error(line, "Sequence item requires a nested block");
                }
                items.add(parseBlock(current().indent()));
                continue;
            }

            if (looksLikeInlineMapping(itemBody)) {
                int itemIndent = indent + 2;
                Map<String, Object> itemMap = new LinkedHashMap<String, Object>();
                KeyValue keyValue = parseKeyValue(itemBody, line.number());
                itemMap.put(keyValue.key(), resolveValue(keyValue.valueText(), itemIndent));
                items.add(parseMapping(itemIndent, itemMap));
                continue;
            }

            items.add(parseScalar(itemBody, line.number()));
        }
        return items;
    }

    private Object resolveValue(String valueText, int parentIndent) {
        if (valueText != null && !valueText.isEmpty()) {
            return parseScalar(valueText, currentLineNumberOrParent());
        }
        if (hasNestedBlock(parentIndent)) {
            return parseBlock(current().indent());
        }
        return null;
    }

    private int currentLineNumberOrParent() {
        if (!hasCurrent()) {
            return lines.isEmpty() ? 1 : lines.get(lines.size() - 1).number();
        }
        return current().number();
    }

    private Object parseScalar(String valueText, int lineNumber) {
        String trimmed = valueText.trim();
        if (trimmed.isEmpty()) {
            return "";
        }
        if ((trimmed.startsWith("\"") && trimmed.endsWith("\"")) || (trimmed.startsWith("'") && trimmed.endsWith("'"))) {
            return unquote(trimmed, lineNumber);
        }
        if ("null".equalsIgnoreCase(trimmed) || "~".equals(trimmed)) {
            return null;
        }
        if ("true".equalsIgnoreCase(trimmed)) {
            return Boolean.TRUE;
        }
        if ("false".equalsIgnoreCase(trimmed)) {
            return Boolean.FALSE;
        }
        if (trimmed.matches("-?[0-9]+")) {
            try {
                long value = Long.parseLong(trimmed);
                if (value >= Integer.MIN_VALUE && value <= Integer.MAX_VALUE) {
                    return Integer.valueOf((int) value);
                }
                return Long.valueOf(value);
            } catch (NumberFormatException exception) {
                throw new YamlParseException("Invalid integer at line " + lineNumber + ": " + trimmed, exception);
            }
        }
        if (trimmed.matches("-?[0-9]+\\.[0-9]+")) {
            try {
                return Double.valueOf(trimmed);
            } catch (NumberFormatException exception) {
                throw new YamlParseException("Invalid number at line " + lineNumber + ": " + trimmed, exception);
            }
        }
        return trimmed;
    }

    private String unquote(String value, int lineNumber) {
        char quote = value.charAt(0);
        String body = value.substring(1, value.length() - 1);
        if (quote == '\'') {
            return body.replace("''", "'");
        }

        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < body.length(); i++) {
            char current = body.charAt(i);
            if (current != '\\') {
                builder.append(current);
                continue;
            }
            if (i + 1 >= body.length()) {
                throw new YamlParseException("Invalid escape at line " + lineNumber);
            }
            char next = body.charAt(++i);
            if (next == 'n') {
                builder.append('\n');
            } else if (next == 'r') {
                builder.append('\r');
            } else if (next == 't') {
                builder.append('\t');
            } else if (next == '\\') {
                builder.append('\\');
            } else if (next == '"') {
                builder.append('"');
            } else {
                builder.append(next);
            }
        }
        return builder.toString();
    }

    private KeyValue parseKeyValue(String content, int lineNumber) {
        int separator = content.indexOf(':');
        if (separator <= 0) {
            throw new YamlParseException("Expected 'key: value' at line " + lineNumber);
        }
        String key = content.substring(0, separator).trim();
        String valueText = content.substring(separator + 1).trim();
        if (key.isEmpty()) {
            throw new YamlParseException("Key must not be empty at line " + lineNumber);
        }
        return new KeyValue(key, valueText);
    }

    private boolean hasNestedBlock(int parentIndent) {
        return hasCurrent() && current().indent() > parentIndent;
    }

    private boolean looksLikeInlineMapping(String text) {
        String trimmed = text.trim();
        if (trimmed.startsWith("\"") || trimmed.startsWith("'")) {
            return false;
        }
        return trimmed.indexOf(':') > 0;
    }

    private boolean isSequenceLine(Line line, int indent) {
        return line.indent() == indent && ("-".equals(line.content()) || line.content().startsWith("- "));
    }

    private String sequenceItemBody(String content) {
        if ("-".equals(content)) {
            return "";
        }
        return content.substring(2).trim();
    }

    private List<Line> preprocess(String yaml) {
        String[] rawLines = yaml.split("\\R", -1);
        List<Line> prepared = new ArrayList<Line>();
        for (int i = 0; i < rawLines.length; i++) {
            String rawLine = rawLines[i];
            if (rawLine.indexOf('\t') >= 0) {
                throw new YamlParseException("Tabs are not supported in YAML indentation at line " + (i + 1));
            }
            String withoutComment = stripComment(rawLine);
            if (withoutComment.trim().isEmpty()) {
                continue;
            }
            int indent = countIndent(withoutComment);
            prepared.add(new Line(i + 1, indent, withoutComment.substring(indent)));
        }
        return prepared;
    }

    private String stripComment(String line) {
        boolean inSingleQuotes = false;
        boolean inDoubleQuotes = false;
        for (int i = 0; i < line.length(); i++) {
            char current = line.charAt(i);
            if (current == '\'' && !inDoubleQuotes) {
                inSingleQuotes = !inSingleQuotes;
                continue;
            }
            if (current == '"' && !inSingleQuotes && !isEscaped(line, i)) {
                inDoubleQuotes = !inDoubleQuotes;
                continue;
            }
            if (current == '#' && !inSingleQuotes && !inDoubleQuotes) {
                if (i == 0 || Character.isWhitespace(line.charAt(i - 1))) {
                    return line.substring(0, i);
                }
            }
        }
        return line;
    }

    private boolean isEscaped(String value, int index) {
        int backslashes = 0;
        for (int i = index - 1; i >= 0 && value.charAt(i) == '\\'; i--) {
            backslashes++;
        }
        return backslashes % 2 == 1;
    }

    private int countIndent(String line) {
        int indent = 0;
        while (indent < line.length() && line.charAt(indent) == ' ') {
            indent++;
        }
        return indent;
    }

    private boolean hasCurrent() {
        return index < lines.size();
    }

    private Line current() {
        return lines.get(index);
    }

    private void advance() {
        index++;
    }

    private YamlParseException error(Line line, String message) {
        return new YamlParseException(message + " at line " + line.number());
    }

    private record Line(int number, int indent, String content) {
    }

    private record KeyValue(String key, String valueText) {
    }
}
