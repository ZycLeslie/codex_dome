package com.codexdome.graphquery;

import com.codexdome.graphquery.validation.ValidationError;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

public final class GraphQueryCompilerSelfTest {
    private static final Path EXAMPLE_DIR = Path.of("src/test/resources/examples");

    private GraphQueryCompilerSelfTest() {
    }

    public static void main(String[] args) throws Exception {
        GraphQueryCompiler compiler = new GraphQueryCompiler();
        shouldGenerateSingleChain(compiler);
        shouldGenerateBranchingQueryWithUntypedEdge(compiler);
        shouldRejectNonContiguousPath(compiler);
        shouldRejectUnknownReturnReference(compiler);
        System.out.println("GraphQueryCompilerSelfTest passed");
    }

    private static void shouldGenerateSingleChain(GraphQueryCompiler compiler) throws IOException {
        GeneratedCypherQuery generated = compiler.compileYamlToCypher(readExample("single-chain.yaml"));
        String expectedQuery = String.join("\n",
                "MATCH path_abc = (A:Account)-[ab:OWNS]->(B:Service)-[bc:CALLS]->(C:Dataset)",
                "WHERE A.id = $node_A_id",
                "  AND A.tenantId = $node_A_prop_tenantId",
                "  AND C.env = $node_C_prop_env",
                "  AND ab.id = $edge_ab_id",
                "  AND ab.active = $edge_ab_prop_active",
                "  AND bc.latencyTier = $edge_bc_prop_latencyTier",
                "RETURN path_abc AS primaryPath,",
                "       B AS sharedNode,",
                "       bc AS terminalEdge",
                "LIMIT 25");
        TestSupport.assertEquals(expectedQuery, generated.query(), "Single-chain query did not match");
        TestSupport.assertMapContains(generated.params(), "node_A_id", "account-1");
        TestSupport.assertMapContains(generated.params(), "node_A_prop_tenantId", "tenant-01");
        TestSupport.assertMapContains(generated.params(), "node_C_prop_env", "prod");
        TestSupport.assertMapContains(generated.params(), "edge_ab_id", "rel-ab");
        TestSupport.assertMapContains(generated.params(), "edge_ab_prop_active", Boolean.TRUE);
        TestSupport.assertMapContains(generated.params(), "edge_bc_prop_latencyTier", "gold");
    }

    private static void shouldGenerateBranchingQueryWithUntypedEdge(GraphQueryCompiler compiler) throws IOException {
        GeneratedCypherQuery generated = compiler.compileYamlToCypher(readExample("branching.yaml"));
        String expectedQuery = String.join("\n",
                "MATCH path_abc = (A:Account)-[ab]->(B:Service:Shared)-[bc:CALLS]->(C)",
                "MATCH path_bd = (B:Service:Shared)-[bd]->(D)",
                "WHERE B.id = $node_B_id",
                "  AND C.status = $node_C_prop_status",
                "  AND D.region = $node_D_prop_region",
                "  AND ab.enabled = $edge_ab_prop_enabled",
                "  AND bd.id = $edge_bd_id",
                "RETURN path_abc AS path_abc,",
                "       path_bd AS path_bd",
                "LIMIT 10");
        TestSupport.assertEquals(expectedQuery, generated.query(), "Branching query did not match");
        TestSupport.assertContains(generated.query(), "-[ab]->", "Untyped edge should omit relation type");
        TestSupport.assertMapContains(generated.params(), "node_B_id", "node-b");
        TestSupport.assertMapContains(generated.params(), "node_C_prop_status", "live");
        TestSupport.assertMapContains(generated.params(), "node_D_prop_region", "cn");
        TestSupport.assertMapContains(generated.params(), "edge_ab_prop_enabled", Boolean.TRUE);
        TestSupport.assertMapContains(generated.params(), "edge_bd_id", "rel-bd");
    }

    private static void shouldRejectNonContiguousPath(GraphQueryCompiler compiler) throws IOException {
        try {
            compiler.compileYamlToCypher(readExample("invalid-non-contiguous.yaml"));
            TestSupport.fail("Expected invalid non-contiguous path to fail validation");
        } catch (GraphQueryValidationException exception) {
            assertHasError(exception.errors(), "query.paths[0].edges[1]", "path is not continuous");
        }
    }

    private static void shouldRejectUnknownReturnReference(GraphQueryCompiler compiler) throws IOException {
        try {
            compiler.compileYamlToCypher(readExample("invalid-return.yaml"));
            TestSupport.fail("Expected invalid return reference to fail validation");
        } catch (GraphQueryValidationException exception) {
            assertHasError(exception.errors(), "query.return.items[0].ref", "unknown node reference");
        }
    }

    private static void assertHasError(List<ValidationError> errors, String field, String messageFragment) {
        for (ValidationError error : errors) {
            if (field.equals(error.field()) && error.message().contains(messageFragment)) {
                return;
            }
        }
        TestSupport.fail("Expected validation error for field '" + field + "' containing '" + messageFragment + "'");
    }

    private static String readExample(String fileName) throws IOException {
        return Files.readString(EXAMPLE_DIR.resolve(fileName));
    }
}
