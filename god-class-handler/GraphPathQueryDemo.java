public class GraphPathQueryDemo {

    public static void main(String[] args) {
        GraphQueryService service = new GraphQueryService("Node", "REL");

        print("节点汇总查询", service.buildNodeSummaryQuery("A"));
        print("边汇总查询", service.buildEdgeSummaryQuery("A", "B"));
        print("直接路径查询 A-B-C", service.buildDirectPathQuery("A-B-C"));
        print("分支路径查询 A-B-C,B-D", service.buildBranchPathQuery("A-B-C,B-D"));

        for (String arg : args) {
            print("自定义输入 " + arg, service.buildBranchPathQuery(arg));
        }
    }

    private static void print(String title, GraphQueryService.CypherQuery query) {
        System.out.println("=== " + title + " ===");
        System.out.println(query.statement());
        System.out.println("params = " + query.params());
        System.out.println();
    }
}
