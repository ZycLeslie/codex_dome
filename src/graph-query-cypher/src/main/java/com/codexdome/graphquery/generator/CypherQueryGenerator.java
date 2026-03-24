package com.codexdome.graphquery.generator;

import com.codexdome.graphquery.GeneratedCypherQuery;
import com.codexdome.graphquery.model.CompiledGraphQuery;
import com.codexdome.graphquery.model.CompiledPath;
import com.codexdome.graphquery.model.CompiledReturnItem;
import com.codexdome.graphquery.model.Direction;
import com.codexdome.graphquery.model.EdgeSpec;
import com.codexdome.graphquery.model.NodeSpec;
import com.codexdome.graphquery.model.ReturnItemKind;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Generates parameterized Cypher statements from a validated compiled query model.
 */
public final class CypherQueryGenerator {
    /**
     * Renders the full Cypher statement and the corresponding parameter map.
     *
     * @param query validated compiled query model
     * @return generated Cypher statement and parameters
     */
    public GeneratedCypherQuery generate(CompiledGraphQuery query) {
        StringBuilder statement = new StringBuilder();
        Map<String, Object> params = new LinkedHashMap<String, Object>();

        appendMatchClauses(statement, query);
        appendWhereClause(statement, params, query);
        appendReturnClause(statement, query.returnItems());
        appendLimit(statement, query.limit());

        return new GeneratedCypherQuery(statement.toString(), params);
    }

    private void appendMatchClauses(StringBuilder statement, CompiledGraphQuery query) {
        for (int pathIndex = 0; pathIndex < query.paths().size(); pathIndex++) {
            if (pathIndex > 0) {
                statement.append('\n');
            }
            CompiledPath path = query.paths().get(pathIndex);
            statement.append("MATCH ").append(path.alias()).append(" = ");
            appendPathPattern(statement, path, query.nodes(), query.edges());
        }
    }

    private void appendPathPattern(StringBuilder statement,
                                   CompiledPath path,
                                   Map<String, NodeSpec> nodes,
                                   Map<String, EdgeSpec> edges) {
        for (int nodeIndex = 0; nodeIndex < path.nodeAliases().size(); nodeIndex++) {
            String nodeAlias = path.nodeAliases().get(nodeIndex);
            NodeSpec node = nodes.get(nodeAlias);
            statement.append('(').append(nodeAlias);
            for (String label : node.labels()) {
                statement.append(':').append(label);
            }
            statement.append(')');

            if (nodeIndex < path.edgeAliases().size()) {
                String edgeAlias = path.edgeAliases().get(nodeIndex);
                EdgeSpec edge = edges.get(edgeAlias);
                appendEdgePattern(statement, edgeAlias, edge);
            }
        }
    }

    private void appendEdgePattern(StringBuilder statement, String edgeAlias, EdgeSpec edge) {
        StringBuilder pattern = new StringBuilder();
        pattern.append('[').append(edgeAlias);
        // The type is optional by design. Keeping the named relationship variable even when the
        // type is absent lets the caller filter or return the edge while still producing valid
        // Cypher such as -[ab]-> instead of forcing a synthetic wildcard type.
        if (edge.type() != null) {
            pattern.append(':').append(edge.type());
        }
        pattern.append(']');

        if (edge.direction() == Direction.INBOUND) {
            statement.append("<-").append(pattern).append('-');
        } else if (edge.direction() == Direction.UNDIRECTED) {
            statement.append('-').append(pattern).append('-');
        } else {
            statement.append('-').append(pattern).append("->");
        }
    }

    private void appendWhereClause(StringBuilder statement,
                                   Map<String, Object> params,
                                   CompiledGraphQuery query) {
        List<String> predicates = new ArrayList<String>();
        // Shared nodes and edges may appear in multiple MATCH paths. WHERE predicates are emitted
        // once per named entity so the generated query stays stable and avoids duplicate filters.
        for (Map.Entry<String, NodeSpec> entry : query.nodes().entrySet()) {
            appendPredicates(predicates, params, "node", entry.getKey(), entry.getValue().id(), entry.getValue().properties());
        }
        for (Map.Entry<String, EdgeSpec> entry : query.edges().entrySet()) {
            appendPredicates(predicates, params, "edge", entry.getKey(), entry.getValue().id(), entry.getValue().properties());
        }

        if (predicates.isEmpty()) {
            return;
        }

        statement.append('\n').append("WHERE ").append(predicates.get(0));
        for (int index = 1; index < predicates.size(); index++) {
            statement.append('\n').append("  AND ").append(predicates.get(index));
        }
    }

    private void appendPredicates(List<String> predicates,
                                  Map<String, Object> params,
                                  String entityKind,
                                  String alias,
                                  Object id,
                                  Map<String, Object> properties) {
        // Parameter names follow the spec's stable pattern:
        //   node_<alias>_id / node_<alias>_prop_<property>
        //   edge_<alias>_id / edge_<alias>_prop_<property>
        // This keeps the output readable and prevents collisions between node and edge filters.
        if (id != null) {
            String paramName = entityKind + "_" + alias + "_id";
            params.put(paramName, id);
            predicates.add(alias + ".id = $" + paramName);
        }
        for (Map.Entry<String, Object> property : properties.entrySet()) {
            String paramName = entityKind + "_" + alias + "_prop_" + property.getKey();
            params.put(paramName, property.getValue());
            predicates.add(alias + "." + property.getKey() + " = $" + paramName);
        }
    }

    private void appendReturnClause(StringBuilder statement, List<CompiledReturnItem> items) {
        statement.append('\n').append("RETURN ");
        for (int index = 0; index < items.size(); index++) {
            CompiledReturnItem item = items.get(index);
            if (index > 0) {
                statement.append(",\n       ");
            }
            String source = sourceAlias(item);
            statement.append(source).append(" AS ").append(item.alias());
        }
    }

    private String sourceAlias(CompiledReturnItem item) {
        if (item.kind() == ReturnItemKind.PATH || item.kind() == ReturnItemKind.NODE || item.kind() == ReturnItemKind.EDGE) {
            return item.ref();
        }
        throw new IllegalArgumentException("Unsupported return item kind: " + item.kind());
    }

    private void appendLimit(StringBuilder statement, Integer limit) {
        if (limit != null) {
            statement.append('\n').append("LIMIT ").append(limit.intValue());
        }
    }
}
