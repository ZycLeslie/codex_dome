import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public final class GraphQueryService {
    private final String nodeLabel;
    private final String relationType;

    public GraphQueryService(String nodeLabel, String relationType) {
        this.nodeLabel = validateIdentifier(nodeLabel, "nodeLabel");
        this.relationType = validateIdentifier(relationType, "relationType");
    }

    public CypherQuery buildNodeSummaryQuery(String nodeId) {
        Map<String, Object> params = new LinkedHashMap<String, Object>();
        params.put("nodeId", requireText(nodeId, "nodeId"));

        String statement = "MATCH (n:" + nodeLabel + " {id: $nodeId})\n"
                + "OPTIONAL MATCH (n)-[out:" + relationType + "]->()\n"
                + "WITH n, count(out) AS outEdgeCount\n"
                + "OPTIONAL MATCH ()-[in:" + relationType + "]->(n)\n"
                + "RETURN n.id AS nodeId,\n"
                + "       outEdgeCount,\n"
                + "       count(in) AS inEdgeCount,\n"
                + "       outEdgeCount + count(in) AS totalEdgeCount";
        return new CypherQuery(statement, params);
    }

    public CypherQuery buildEdgeSummaryQuery(String fromNodeId, String toNodeId) {
        Map<String, Object> params = new LinkedHashMap<String, Object>();
        params.put("fromNodeId", requireText(fromNodeId, "fromNodeId"));
        params.put("toNodeId", requireText(toNodeId, "toNodeId"));

        String statement = "MATCH (from:" + nodeLabel + " {id: $fromNodeId})"
                + "-[r:" + relationType + "]->"
                + "(to:" + nodeLabel + " {id: $toNodeId})\n"
                + "RETURN from.id AS fromNodeId,\n"
                + "       to.id AS toNodeId,\n"
                + "       type(r) AS relationType,\n"
                + "       properties(r) AS edgeProperties";
        return new CypherQuery(statement, params);
    }

    public CypherQuery buildDirectPathQuery(String expression) {
        PathSpec path = parseDirectPath(expression);
        return buildPathQuery(path, "p", false, "path");
    }

    public CypherQuery buildBranchPathQuery(String expression) {
        List<PathSpec> branches = parseBranches(expression);
        if (branches.size() == 1) {
            return buildPathQuery(branches.get(0), "p", false, "path");
        }

        StringBuilder statement = new StringBuilder();
        Map<String, Object> params = new LinkedHashMap<String, Object>();
        for (int i = 0; i < branches.size(); i++) {
            if (i > 0) {
                statement.append("\nUNION ALL\n");
            }

            String pathAlias = "p" + i;
            String paramPrefix = "branch" + i;
            CypherQuery branchQuery = buildPathQuery(branches.get(i), pathAlias, true, paramPrefix);
            statement.append(branchQuery.statement());
            params.putAll(branchQuery.params());
        }
        return new CypherQuery(statement.toString(), params);
    }

    private CypherQuery buildPathQuery(PathSpec path, String pathAlias, boolean includeBranchName, String paramPrefix) {
        StringBuilder statement = new StringBuilder();
        Map<String, Object> params = new LinkedHashMap<String, Object>();

        statement.append("MATCH ").append(pathAlias).append(" = ");
        appendPathPattern(statement, params, path.nodes(), paramPrefix);
        statement.append("\nRETURN ");
        if (includeBranchName) {
            statement.append("'").append(path.expression()).append("' AS branch,\n       ");
        }
        statement.append(pathAlias).append(" AS path,\n")
                .append("       [node IN nodes(").append(pathAlias).append(") | node.id] AS nodeIds,\n")
                .append("       [rel IN relationships(").append(pathAlias).append(") | properties(rel)] AS edgeSummaries");
        return new CypherQuery(statement.toString(), params);
    }

    private void appendPathPattern(StringBuilder statement, Map<String, Object> params,
                                   List<String> nodes, String paramPrefix) {
        for (int i = 0; i < nodes.size(); i++) {
            String paramName = paramPrefix + "Node" + i;
            params.put(paramName, nodes.get(i));
            statement.append("(n").append(i).append(":").append(nodeLabel)
                    .append(" {id: $").append(paramName).append("})");
            if (i < nodes.size() - 1) {
                statement.append("-[:").append(relationType).append("]->");
            }
        }
    }

    private List<PathSpec> parseBranches(String expression) {
        String normalized = normalize(expression);
        if (normalized.isEmpty()) {
            throw new IllegalArgumentException("query expression must not be empty");
        }

        List<PathSpec> branches = new ArrayList<PathSpec>();
        for (String segment : normalized.split(",")) {
            if (!segment.isEmpty()) {
                branches.add(parsePath(segment));
            }
        }
        if (branches.isEmpty()) {
            throw new IllegalArgumentException("query expression must not be empty");
        }
        return branches;
    }

    private PathSpec parseDirectPath(String expression) {
        String normalized = normalize(expression);
        if (normalized.contains(",")) {
            throw new IllegalArgumentException("direct path query does not support branches: " + expression);
        }
        return parsePath(normalized);
    }

    private PathSpec parsePath(String expression) {
        List<String> rawNodes = Arrays.asList(normalize(expression).split("-"));
        if (rawNodes.size() < 2) {
            throw new IllegalArgumentException("path requires at least two nodes: " + expression);
        }

        List<String> nodes = new ArrayList<String>();
        for (String rawNode : rawNodes) {
            nodes.add(requireText(rawNode, "nodeId"));
        }
        return new PathSpec(String.join("-", nodes), nodes);
    }

    private String normalize(String expression) {
        if (expression == null) {
            return "";
        }
        return expression.replace("，", ",").replace("；", ",").replaceAll("\\s+", "");
    }

    private String requireText(String value, String fieldName) {
        if (value == null || value.trim().isEmpty()) {
            throw new IllegalArgumentException(fieldName + " must not be empty");
        }
        return value.trim();
    }

    private String validateIdentifier(String value, String fieldName) {
        String text = requireText(value, fieldName);
        if (!text.matches("[A-Za-z_][A-Za-z0-9_]*")) {
            throw new IllegalArgumentException(fieldName + " is invalid: " + value);
        }
        return text;
    }

    private static final class PathSpec {
        private final String expression;
        private final List<String> nodes;

        private PathSpec(String expression, List<String> nodes) {
            this.expression = expression;
            this.nodes = Collections.unmodifiableList(new ArrayList<String>(nodes));
        }

        private String expression() {
            return expression;
        }

        private List<String> nodes() {
            return nodes;
        }
    }

    public static final class CypherQuery {
        private final String statement;
        private final Map<String, Object> params;

        public CypherQuery(String statement, Map<String, Object> params) {
            this.statement = statement;
            this.params = Collections.unmodifiableMap(new LinkedHashMap<String, Object>(params));
        }

        public String statement() {
            return statement;
        }

        public Map<String, Object> params() {
            return params;
        }
    }
}
