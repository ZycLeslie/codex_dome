package com.codexdome.graphquery;

import com.codexdome.graphquery.generator.CypherQueryGenerator;
import com.codexdome.graphquery.model.CompiledGraphQuery;
import com.codexdome.graphquery.model.CompiledPath;
import com.codexdome.graphquery.model.CompiledReturnItem;
import com.codexdome.graphquery.model.EdgeSpec;
import com.codexdome.graphquery.model.PathSpec;
import com.codexdome.graphquery.model.QueryDocument;
import com.codexdome.graphquery.model.QuerySpec;
import com.codexdome.graphquery.model.ReturnItemKind;
import com.codexdome.graphquery.model.ReturnItemSpec;
import com.codexdome.graphquery.parser.YamlGraphQueryParser;
import com.codexdome.graphquery.validation.GraphQueryValidator;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Facade for the YAML-to-Cypher pipeline.
 *
 * <p>This entry point keeps parsing, validation, compilation, and query generation separated
 * internally while exposing a small public API to callers.</p>
 */
public final class GraphQueryCompiler {
    private final YamlGraphQueryParser parser;
    private final GraphQueryValidator validator;
    private final CypherQueryGenerator generator;

    /**
     * Creates a compiler with the default parser, validator, and generator implementations.
     */
    public GraphQueryCompiler() {
        this(new YamlGraphQueryParser(), new GraphQueryValidator(), new CypherQueryGenerator());
    }

    GraphQueryCompiler(YamlGraphQueryParser parser,
                       GraphQueryValidator validator,
                       CypherQueryGenerator generator) {
        this.parser = parser;
        this.validator = validator;
        this.generator = generator;
    }

    /**
     * Parses YAML text into the immutable document model.
     *
     * @param yaml YAML text that follows the graph-query schema
     * @return parsed document
     */
    public QueryDocument parseYaml(String yaml) {
        return parser.parse(yaml);
    }

    /**
     * Reads YAML from disk and parses it into the immutable document model.
     *
     * @param yamlPath path to the YAML input file
     * @return parsed document
     */
    public QueryDocument parseYaml(Path yamlPath) {
        try {
            return parseYaml(Files.readString(yamlPath));
        } catch (IOException exception) {
            throw new UncheckedIOException("Failed to read YAML from " + yamlPath, exception);
        }
    }

    /**
     * Validates and compiles a parsed query document into the generator-ready model.
     *
     * @param document parsed query document
     * @return validated compiled query model
     */
    public CompiledGraphQuery compile(QueryDocument document) {
        validator.validate(document);
        return toCompiledQuery(document.query());
    }

    /**
     * Parses, validates, compiles, and generates Cypher from YAML text.
     *
     * @param yaml YAML text that follows the graph-query schema
     * @return generated query and parameters
     */
    public GeneratedCypherQuery compileYamlToCypher(String yaml) {
        return generate(compile(parseYaml(yaml)));
    }

    /**
     * Reads YAML from disk, then parses, validates, compiles, and generates Cypher.
     *
     * @param yamlPath path to the YAML input file
     * @return generated query and parameters
     */
    public GeneratedCypherQuery compileYamlToCypher(Path yamlPath) {
        return generate(compile(parseYaml(yamlPath)));
    }

    /**
     * Generates Cypher from a compiled graph query.
     *
     * @param query validated compiled query model
     * @return generated query and parameters
     */
    public GeneratedCypherQuery generate(CompiledGraphQuery query) {
        return generator.generate(query);
    }

    private CompiledGraphQuery toCompiledQuery(QuerySpec query) {
        Map<String, EdgeSpec> edges = query.edges();
        List<CompiledPath> compiledPaths = new ArrayList<CompiledPath>();
        for (PathSpec path : query.paths()) {
            List<String> nodeAliases = new ArrayList<String>();
            EdgeSpec firstEdge = edges.get(path.edges().get(0));
            nodeAliases.add(firstEdge.from());
            // YAML paths only list edge aliases. After validation has guaranteed that the path is
            // continuous, the compiler can reconstruct the node walk by taking the first source
            // node and then appending each edge's target node in order.
            for (String edgeAlias : path.edges()) {
                EdgeSpec edge = edges.get(edgeAlias);
                nodeAliases.add(edge.to());
            }
            compiledPaths.add(new CompiledPath(path.alias(), nodeAliases, path.edges()));
        }

        List<CompiledReturnItem> compiledReturnItems = new ArrayList<CompiledReturnItem>();
        if (query.returnSpec().items().isEmpty()) {
            // An empty return section means "return every named path" in declaration order.
            for (CompiledPath path : compiledPaths) {
                compiledReturnItems.add(new CompiledReturnItem(ReturnItemKind.PATH, path.alias(), path.alias()));
            }
        } else {
            for (ReturnItemSpec item : query.returnSpec().items()) {
                compiledReturnItems.add(new CompiledReturnItem(item.kind(), item.ref(), item.alias()));
            }
        }

        return new CompiledGraphQuery(
                new LinkedHashMap<String, com.codexdome.graphquery.model.NodeSpec>(query.nodes()),
                new LinkedHashMap<String, EdgeSpec>(query.edges()),
                compiledPaths,
                compiledReturnItems,
                query.limit()
        );
    }
}
