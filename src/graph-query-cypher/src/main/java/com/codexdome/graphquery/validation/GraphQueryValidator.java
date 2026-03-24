package com.codexdome.graphquery.validation;

import com.codexdome.graphquery.GraphQueryValidationException;
import com.codexdome.graphquery.model.EdgeSpec;
import com.codexdome.graphquery.model.NodeSpec;
import com.codexdome.graphquery.model.PathSpec;
import com.codexdome.graphquery.model.QueryDocument;
import com.codexdome.graphquery.model.QuerySpec;
import com.codexdome.graphquery.model.ReturnItemKind;
import com.codexdome.graphquery.model.ReturnItemSpec;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.regex.Pattern;

public final class GraphQueryValidator {
    private static final Pattern IDENTIFIER = Pattern.compile("[A-Za-z_][A-Za-z0-9_]*");

    public void validate(QueryDocument document) {
        List<ValidationError> errors = new ArrayList<ValidationError>();
        if (document == null) {
            errors.add(new ValidationError("document", "document must not be null"));
            throw new GraphQueryValidationException(errors);
        }

        if (document.version() != 1) {
            errors.add(new ValidationError("version", "only version 1 is supported"));
        }

        QuerySpec query = document.query();
        if (query == null) {
            errors.add(new ValidationError("query", "query must not be null"));
            throwIfAny(errors);
            return;
        }

        validateNodes(query.nodes(), errors);
        validateEdges(query.nodes(), query.edges(), errors);
        validatePaths(query.edges(), query.paths(), errors);
        validateGraphAliasCollisions(query.nodes(), query.edges(), query.paths(), errors);
        validateReturnItems(query.nodes(), query.edges(), query.paths(), query.returnSpec().items(), errors);
        validateLimit(query.limit(), errors);
        throwIfAny(errors);
    }

    private void validateNodes(Map<String, NodeSpec> nodes, List<ValidationError> errors) {
        if (nodes.isEmpty()) {
            errors.add(new ValidationError("query.nodes", "at least one node must be defined"));
            return;
        }

        for (Map.Entry<String, NodeSpec> entry : nodes.entrySet()) {
            String alias = entry.getKey();
            NodeSpec node = entry.getValue();
            if (!isValidIdentifier(alias)) {
                errors.add(new ValidationError("query.nodes." + alias, "node alias must be a valid identifier"));
            }
            if (node == null) {
                errors.add(new ValidationError("query.nodes." + alias, "node definition must not be null"));
                continue;
            }
            validateIdentifierList("query.nodes." + alias + ".labels", node.labels(), errors, "label");
            validateScalar("query.nodes." + alias + ".id", node.id(), errors);
            validateProperties("query.nodes." + alias + ".properties", node.properties(), errors);
        }
    }

    private void validateEdges(Map<String, NodeSpec> nodes,
                               Map<String, EdgeSpec> edges,
                               List<ValidationError> errors) {
        if (edges.isEmpty()) {
            errors.add(new ValidationError("query.edges", "at least one edge must be defined"));
            return;
        }

        for (Map.Entry<String, EdgeSpec> entry : edges.entrySet()) {
            String alias = entry.getKey();
            EdgeSpec edge = entry.getValue();
            if (!isValidIdentifier(alias)) {
                errors.add(new ValidationError("query.edges." + alias, "edge alias must be a valid identifier"));
            }
            if (edge == null) {
                errors.add(new ValidationError("query.edges." + alias, "edge definition must not be null"));
                continue;
            }
            if (!isValidIdentifier(edge.from())) {
                errors.add(new ValidationError("query.edges." + alias + ".from", "from must be a valid identifier"));
            } else if (!nodes.containsKey(edge.from())) {
                errors.add(new ValidationError("query.edges." + alias + ".from", "from references unknown node '" + edge.from() + "'"));
            }
            if (!isValidIdentifier(edge.to())) {
                errors.add(new ValidationError("query.edges." + alias + ".to", "to must be a valid identifier"));
            } else if (!nodes.containsKey(edge.to())) {
                errors.add(new ValidationError("query.edges." + alias + ".to", "to references unknown node '" + edge.to() + "'"));
            }
            if (edge.direction() == null) {
                errors.add(new ValidationError("query.edges." + alias + ".direction", "direction must be provided"));
            }
            if (edge.type() != null && !isValidIdentifier(edge.type())) {
                errors.add(new ValidationError("query.edges." + alias + ".type", "type must be a valid identifier"));
            }
            validateScalar("query.edges." + alias + ".id", edge.id(), errors);
            validateProperties("query.edges." + alias + ".properties", edge.properties(), errors);
        }
    }

    private void validatePaths(Map<String, EdgeSpec> edges,
                               List<PathSpec> paths,
                               List<ValidationError> errors) {
        if (paths.isEmpty()) {
            errors.add(new ValidationError("query.paths", "at least one path must be defined"));
            return;
        }

        Set<String> pathAliases = new HashSet<String>();
        for (int index = 0; index < paths.size(); index++) {
            PathSpec path = paths.get(index);
            String fieldPrefix = "query.paths[" + index + "]";
            if (path == null) {
                errors.add(new ValidationError(fieldPrefix, "path definition must not be null"));
                continue;
            }
            if (!isValidIdentifier(path.alias())) {
                errors.add(new ValidationError(fieldPrefix + ".alias", "path alias must be a valid identifier"));
            } else if (!pathAliases.add(path.alias())) {
                errors.add(new ValidationError(fieldPrefix + ".alias", "duplicate path alias '" + path.alias() + "'"));
            }
            if (path.edges().isEmpty()) {
                errors.add(new ValidationError(fieldPrefix + ".edges", "path must reference at least one edge"));
                continue;
            }

            EdgeSpec previous = null;
            for (int edgeIndex = 0; edgeIndex < path.edges().size(); edgeIndex++) {
                String edgeAlias = path.edges().get(edgeIndex);
                String edgeField = fieldPrefix + ".edges[" + edgeIndex + "]";
                if (!isValidIdentifier(edgeAlias)) {
                    errors.add(new ValidationError(edgeField, "edge reference must be a valid identifier"));
                    previous = null;
                    continue;
                }
                EdgeSpec current = edges.get(edgeAlias);
                if (current == null) {
                    errors.add(new ValidationError(edgeField, "unknown edge reference '" + edgeAlias + "'"));
                    previous = null;
                    continue;
                }
                if (previous != null && !previous.to().equals(current.from())) {
                    errors.add(new ValidationError(edgeField,
                            "path is not continuous: edge '" + previous.to() + "' to '" + current.from() + "' does not connect"));
                }
                previous = current;
            }
        }
    }

    private void validateReturnItems(Map<String, NodeSpec> nodes,
                                     Map<String, EdgeSpec> edges,
                                     List<PathSpec> paths,
                                     List<ReturnItemSpec> items,
                                     List<ValidationError> errors) {
        if (items.isEmpty()) {
            return;
        }

        Set<String> pathAliases = new HashSet<String>();
        for (PathSpec path : paths) {
            pathAliases.add(path.alias());
        }

        Set<String> outputAliases = new HashSet<String>();
        for (int index = 0; index < items.size(); index++) {
            ReturnItemSpec item = items.get(index);
            String fieldPrefix = "query.return.items[" + index + "]";
            if (item == null) {
                errors.add(new ValidationError(fieldPrefix, "return item must not be null"));
                continue;
            }
            if (item.kind() == null) {
                errors.add(new ValidationError(fieldPrefix + ".kind", "kind must be one of PATH, NODE, EDGE"));
            }
            if (!isValidIdentifier(item.alias())) {
                errors.add(new ValidationError(fieldPrefix + ".alias", "output alias must be a valid identifier"));
            } else if (!outputAliases.add(item.alias())) {
                errors.add(new ValidationError(fieldPrefix + ".alias", "duplicate output alias '" + item.alias() + "'"));
            }

            ReturnItemKind kind = item.kind();
            String ref = item.ref();
            if (!isValidIdentifier(ref)) {
                errors.add(new ValidationError(fieldPrefix + ".ref", "ref must be a valid identifier"));
                continue;
            }
            if (kind == ReturnItemKind.PATH && !pathAliases.contains(ref)) {
                errors.add(new ValidationError(fieldPrefix + ".ref", "unknown path reference '" + ref + "'"));
            } else if (kind == ReturnItemKind.NODE && !nodes.containsKey(ref)) {
                errors.add(new ValidationError(fieldPrefix + ".ref", "unknown node reference '" + ref + "'"));
            } else if (kind == ReturnItemKind.EDGE && !edges.containsKey(ref)) {
                errors.add(new ValidationError(fieldPrefix + ".ref", "unknown edge reference '" + ref + "'"));
            }
        }
    }

    private void validateGraphAliasCollisions(Map<String, NodeSpec> nodes,
                                              Map<String, EdgeSpec> edges,
                                              List<PathSpec> paths,
                                              List<ValidationError> errors) {
        Set<String> usedAliases = new HashSet<String>();
        for (String nodeAlias : nodes.keySet()) {
            usedAliases.add(nodeAlias);
        }
        for (String edgeAlias : edges.keySet()) {
            if (!usedAliases.add(edgeAlias)) {
                errors.add(new ValidationError("query.edges." + edgeAlias,
                        "edge alias collides with another graph alias '" + edgeAlias + "'"));
            }
        }
        for (int index = 0; index < paths.size(); index++) {
            String pathAlias = paths.get(index).alias();
            if (pathAlias != null && !usedAliases.add(pathAlias)) {
                errors.add(new ValidationError("query.paths[" + index + "].alias",
                        "path alias collides with another graph alias '" + pathAlias + "'"));
            }
        }
    }

    private void validateLimit(Integer limit, List<ValidationError> errors) {
        if (limit != null && limit.intValue() <= 0) {
            errors.add(new ValidationError("query.limit", "limit must be greater than 0"));
        }
    }

    private void validateIdentifierList(String field,
                                        List<String> values,
                                        List<ValidationError> errors,
                                        String elementName) {
        for (int index = 0; index < values.size(); index++) {
            String value = values.get(index);
            if (!isValidIdentifier(value)) {
                errors.add(new ValidationError(field + "[" + index + "]", elementName + " must be a valid identifier"));
            }
        }
    }

    private void validateProperties(String field,
                                    Map<String, Object> properties,
                                    List<ValidationError> errors) {
        for (Map.Entry<String, Object> entry : properties.entrySet()) {
            String key = entry.getKey();
            if ("id".equals(key)) {
                errors.add(new ValidationError(field + "." + key, "id must use the dedicated id field"));
            }
            if (!isValidIdentifier(key)) {
                errors.add(new ValidationError(field + "." + key, "property key must be a valid identifier"));
            }
            validateScalar(field + "." + key, entry.getValue(), errors);
        }
    }

    private void validateScalar(String field, Object value, List<ValidationError> errors) {
        if (value == null) {
            return;
        }
        if (!(value instanceof String) && !(value instanceof Number) && !(value instanceof Boolean)) {
            errors.add(new ValidationError(field, "value must be a scalar"));
        }
    }

    private boolean isValidIdentifier(String value) {
        return value != null && IDENTIFIER.matcher(value).matches();
    }

    private void throwIfAny(List<ValidationError> errors) {
        if (!errors.isEmpty()) {
            throw new GraphQueryValidationException(errors);
        }
    }
}
