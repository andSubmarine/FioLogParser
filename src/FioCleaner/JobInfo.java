import java.util.HashMap;
import java.util.TreeMap;

public class JobInfo {

    public String NAME;
    public String IOPS;
    public String BW;
    public String LAT;
    public TreeMap<Double, Double> CLATpercentiles;
    public String CPU;
    public String DATE;

    public JobInfo(String jobname){
        NAME = jobname;
    }

}
