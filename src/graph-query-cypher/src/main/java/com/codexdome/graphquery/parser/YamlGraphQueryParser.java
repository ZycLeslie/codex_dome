package com.codexdome.graphquery.parser;

import com.codexdome.graphquery.YamlParseException;
import com.codexdome.graphquery.model.Direction;
import com.codexdome.graphquery.model.EdgeSpec;
import com.codexdome.graphquery.model.NodeSpec;
import com.codexdome.graphquery.model.PathSpec;
import com.codexdome.graphquery.model.QueryDocument;
import com.codexdome.graphquery.model.QuerySpec;
import com.codexdome.graphquery.model.ReturnItemKind;
import com.codexdome.graphquery.model.ReturnItemSpec;
import com.codexdome.graphquery.model.ReturnSpec;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public final class YamlGraphQueryParser {
    private final SimpleYamlParser yamlParser;

    public YamlGraphQueryParser() {
        this(new SimpleYamlParser());
    }

    YamlGraphQueryParser(SimpleYamlParser yamlParser) {
        this.yamlParser = yamlParser;
    }

    public QueryDocument parse(String yaml) {
        Map<String, Object> root = requireMap(yamlParser.parse(yaml), "root");
        Integer version = requireInteger(root.get("version"), "version");
        QuerySpec query = parseQuerySpec(requireMap(root.get("query"), "query"));
        return new QueryDocument(version.intValue(), query);
    }

    private QuerySpec parseQuerySpec(Map<String, Object> queryMap) {
        Map<String, NodeSpec> nodes = parseNodes(asMapOrEmpty(queryMap.get("nodes"), "query.nodes"));
        Map<String, EdgeSpec> edges = parseEdges(asMapOrEmpty(queryMap.get("edges"), "query.edges"));
        List<PathSpec> paths = parsePaths(asListOrEmpty(queryMap.get("paths"), "query.paths"));
        ReturnSpec returnSpec = parseReturnSpec(asMapOrEmpty(queryMap.get("return"), "query.return"));
        Integer limit = optionalInteger(queryMap.get("limit"), "query.limit");
        return new QuerySpec(nodes, edges, paths, returnSpec, limit);
    }

    private Map<String, NodeSpec> parseNodes(Map<String, Object> nodesMap) {
        Map<String, NodeSpec> nodes = new LinkedHashMap<String, NodeSpec>();
        for (Map.Entry<String, Object> entry : nodesMap.entrySet()) {
            String field = "query.nodes." + entry.getKey();
            Map<String, Object> nodeMap = requireMap(entry.getValue(), field);
            nodes.put(entry.getKey(), new NodeSpec(
                    stringList(nodeMap.get("labels"), field + ".labels"),
                    optionalScalar(nodeMap.get("id"), field + ".id"),
                    scalarMap(nodeMap.get("properties"), field + ".properties")
            ));
        }
        return nodes;
    }

    private Map<String, EdgeSpec> parseEdges(Map<String, Object> edgesMap) {
        Map<String, EdgeSpec> edges = new LinkedHashMap<String, EdgeSpec>();
        for (Map.Entry<String, Object> entry : edgesMap.entrySet()) {
            String field = "query.edges." + entry.getKey();
            Map<String, Object> edgeMap = requireMap(entry.getValue(), field);
            edges.put(entry.getKey(), new EdgeSpec(
                    optionalString(edgeMap.get("from"), field + ".from"),
                    optionalString(edgeMap.get("to"), field + ".to"),
                    optionalDirection(edgeMap.get("direction"), field + ".direction"),
                    optionalString(edgeMap.get("type"), field + ".type"),
                    optionalScalar(edgeMap.get("id"), field + ".id"),
                    scalarMap(edgeMap.get("properties"), field + ".properties")
            ));
        }
        return edges;
    }

    private List<PathSpec> parsePaths(List<Object> pathItems) {
        List<PathSpec> paths = new ArrayList<PathSpec>();
        for (int index = 0; index < pathItems.size(); index++) {
            String field = "query.paths[" + index + "]";
            Map<String, Object> pathMap = requireMap(pathItems.get(index), field);
            paths.add(new PathSpec(
                    optionalString(pathMap.get("alias"), field + ".alias"),
                    stringList(pathMap.get("edges"), field + ".edges")
            ));
        }
        return paths;
    }

    private ReturnSpec parseReturnSpec(Map<String, Object> returnMap) {
        List<Object> itemValues = asListOrEmpty(returnMap.get("items"), "query.return.items");
        List<ReturnItemSpec> items = new ArrayList<ReturnItemSpec>();
        for (int index = 0; index < itemValues.size(); index++) {
            String field = "query.return.items[" + index + "]";
            Map<String, Object> itemMap = requireMap(itemValues.get(index), field);
            items.add(new ReturnItemSpec(
                    optionalReturnKind(itemMap.get("kind"), field + ".kind"),
                    optionalString(itemMap.get("ref"), field + ".ref"),
                    optionalString(itemMap.get("alias"), field + ".alias")
            ));
        }
        return new ReturnSpec(items);
    }

    private Map<String, Object> scalarMap(Object value, String field) {
        Map<String, Object> source = asMapOrEmpty(value, field);
        Map<String, Object> values = new LinkedHashMap<String, Object>();
        for (Map.Entry<String, Object> entry : source.entrySet()) {
            Object scalar = optionalScalar(entry.getValue(), field + "." + entry.getKey());
            values.put(entry.getKey(), scalar);
        }
        return values;
    }

    private List<String> stringList(Object value, String field) {
        List<Object> values = asListOrEmpty(value, field);
        List<String> strings = new ArrayList<String>();
        for (int i = 0; i < values.size(); i++) {
            Object item = values.get(i);
            if (!(item instanceof String)) {
                throw new YamlParseException(field + "[" + i + "] must be a string");
            }
            strings.add((String) item);
        }
        return strings;
    }

    private Object optionalScalar(Object value, String field) {
        if (value == null) {
            return null;
        }
        if (value instanceof String || value instanceof Number || value instanceof Boolean) {
            return value;
        }
        throw new YamlParseException(field + " must be a scalar");
    }

    private String optionalString(Object value, String field) {
        if (value == null) {
            return null;
        }
        if (!(value instanceof String)) {
            throw new YamlParseException(field + " must be a string");
        }
        return (String) value;
    }

    private Integer optionalInteger(Object value, String field) {
        if (value == null) {
            return null;
        }
        return requireInteger(value, field);
    }

    private Integer requireInteger(Object value, String field) {
        if (!(value instanceof Number)) {
            throw new YamlParseException(field + " must be an integer");
        }
        Number number = (Number) value;
        double asDouble = number.doubleValue();
        int asInteger = number.intValue();
        if (Double.compare(asDouble, (double) asInteger) != 0) {
            throw new YamlParseException(field + " must be an integer");
        }
        return Integer.valueOf(asInteger);
    }

    private Direction optionalDirection(Object value, String field) {
        String raw = optionalString(value, field);
        if (raw == null) {
            return null;
        }
        try {
            return Direction.fromString(raw);
        } catch (IllegalArgumentException exception) {
            throw new YamlParseException(field + " must be one of OUTBOUND, INBOUND, UNDIRECTED");
        }
    }

    private ReturnItemKind optionalReturnKind(Object value, String field) {
        String raw = optionalString(value, field);
        if (raw == null) {
            return null;
        }
        try {
            return ReturnItemKind.fromString(raw);
        } catch (IllegalArgumentException exception) {
            throw new YamlParseException(field + " must be one of PATH, NODE, EDGE");
        }
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> requireMap(Object value, String field) {
        if (!(value instanceof Map<?, ?>)) {
            throw new YamlParseException(field + " must be a mapping");
        }
        return (Map<String, Object>) value;
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> asMapOrEmpty(Object value, String field) {
        if (value == null) {
            return new LinkedHashMap<String, Object>();
        }
        if (!(value instanceof Map<?, ?>)) {
            throw new YamlParseException(field + " must be a mapping");
        }
        return (Map<String, Object>) value;
    }

    @SuppressWarnings("unchecked")
    private List<Object> asListOrEmpty(Object value, String field) {
        if (value == null) {
            return new ArrayList<Object>();
        }
        if (!(value instanceof List<?>)) {
            throw new YamlParseException(field + " must be a list");
        }
        return (List<Object>) value;
    }
}
