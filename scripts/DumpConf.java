import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.Path;
import java.util.Map;

public class DumpConf {
    public static void main(String[] args) throws Exception {
        Configuration conf = new Configuration();
        conf.addResource(new Path("/opt/hive/conf/hive-site.xml"));
        conf.addResource(new Path("/opt/hive/conf/metastore-site.xml"));
        conf.addResource(new Path("/opt/hive/conf/core-site.xml"));
        for (Map.Entry<String, String> e : conf) {
            String v = e.getValue();
            if (v == null) continue;
            if (v.matches(".*\\d+s.*")) {
                System.out.println("SUFFIX: " + e.getKey() + " = " + v);
            }
        }
        System.out.println("--- done ---");
    }
}
