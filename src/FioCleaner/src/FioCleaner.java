import com.sun.org.apache.xpath.internal.operations.Bool;
import javafx.application.Application;
import javafx.application.Platform;
import javafx.embed.swing.JFXPanel;
import javafx.stage.Stage;

import java.io.*;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Scanner;
import java.util.StringTokenizer;
import java.util.TreeMap;
import java.util.function.Supplier;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Stream;


public class FioCleaner{

    public static ArrayList<JobInfo> myFioJobs;
    private static boolean javaFxLaunched = false;

    public static void main(String[] args) {
        CheckArguments(args);

        int numberOfFiles = Integer.parseInt(args[0]);
        File[] inputFiles = new File[numberOfFiles+1];
        for (int i = 1; i < numberOfFiles+1; i++) {
            inputFiles[i] = new File(args[i]);
        }
        int jobs = Integer.parseInt(args[numberOfFiles+1]);
        ArrayList<JobInfo> FioJobs = GetFioObjects(inputFiles, jobs);
        myFioJobs = FioJobs;
        PrintLatexTable(FioJobs);

        //Must be run twice, one for together-chart and one for alone chart...
        //CreateBarCharts instantiates BarChartAlone() when javaFxLaunched flag is true.

        for (int i = 1; i < numberOfFiles; i++) {
            boolean clatExists = DoesClatExist(inputFiles[i].getPath());
            if (clatExists){
                BarChartTogether bct = new BarChartTogether();
                CreateBarCharts(bct.getClass());
                CreateBarCharts(bct.getClass());
            }
        }


    }

    private static void CreateBarCharts(Class<? extends Application> barchartTogether) {
        if (!javaFxLaunched) { //first time
            Platform.setImplicitExit(false);
            new Thread(() ->Application.launch(barchartTogether)).start();
            javaFxLaunched = true;
        } else {
            new JFXPanel(); //Apparently JFX requires a new JFXPanel when closing last app instance.
            Platform.runLater(() -> {
                try {
                    BarChartAlone bca = new BarChartAlone();

                    Application application = bca;
                    Stage primaryStage = new Stage();
                    application.start(primaryStage);
                } catch (Exception e) {
                    e.printStackTrace();
                }
            });
        }
    }


    public static ArrayList<JobInfo> GetFioObjects(File[] inputFiles, int numJobs) {
        //Get jobnames
        ArrayList<JobInfo> result = new ArrayList<>();
        for (int i=1; i < inputFiles.length; i++){
            try {
                Scanner scanner = new Scanner(inputFiles[i]);
                ArrayList<JobInfo> jobs = GetJobNames(numJobs, scanner);

                while(scanner.hasNextLine()){
                    String currentLine = scanner.nextLine();
                    for (JobInfo job : jobs){
                        if (job.NAME.startsWith("warmup")) continue;
                        if (currentLine.startsWith(job.NAME)){
                            ExtractDate(currentLine, job);
                            ExtractBWandIOPS(scanner, job);
                            ExtractLAT(scanner,job);
                            boolean clatExists = DoesClatExist(inputFiles[i].getPath());
                            if (clatExists){
                                ExtractCLATPercentiles(scanner,job);
                            }
                            ExtractCPU(scanner,job);
                            result.add(job);
                        }

                    }
                }
            } catch (FileNotFoundException e) {
                e.printStackTrace();
                return null;
            }
        }
        return result;
    }

    private static void ExtractDate(String line, JobInfo job) {
        String[] splittedLine = line.split(":");
        job.DATE = splittedLine[4].trim() +":"+ splittedLine[5] +":" + splittedLine[6];
    }

    private static JobInfo ExtractCPU(Scanner scanner, JobInfo job) {
        String searchCPU = scanner.nextLine().trim();
        while(!searchCPU.startsWith("cpu")){
            searchCPU = scanner.nextLine().trim();
        }

        Pattern p = Pattern.compile("^\\s*cpu\\s*:\\s*(usr)=([\\d.]*)%?[, ]*(sys)=([\\d.]*)%?[, ]*(ctx)=([\\d.]*)[, ]*(majf)=([\\d.]*)[, ]*(minf)=([\\d.]*)[, ]*$");
        Matcher m = p.matcher(searchCPU);
        if(m.find()){
            job.CPU = m.group(4) + "\\%";
        }

        return job;
    }

    private static boolean DoesClatExist(String fileName) {
        double count = 0,countBuffer=0,countLine=0;
        StringBuilder lineNumber = new StringBuilder();
        BufferedReader br;
        String inputSearch = "clat percentiles";
        String line = "";
        try {
            br = new BufferedReader(new FileReader(fileName));
            try {
                while((line = br.readLine()) != null)
                {
                    countLine++;
                    if (line.contains("clat percentiles")){
                        return true;
                    }

                    count++;
                    countBuffer++;
                    if(countBuffer > 0)
                    {
                        countBuffer = 0;
                        lineNumber.append(countLine).append(",");
                    }
                }
                br.close();
            } catch (IOException e) {
                // TODO Auto-generated catch block
                e.printStackTrace();
            }
        } catch (FileNotFoundException e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
        }
        return false;
    }

    private static JobInfo ExtractCLATPercentiles(Scanner scanner, JobInfo job) {
        Pattern p = Pattern.compile("^(?:[\\s|]*)(?:([0-9.]*)th=\\[\\s*([0-9]*)\\s*\\][, ]*)(?:([0-9.]*)th=\\[\\s*([0-9]*)\\s*\\][, ]*)?(?:([0-9.]*)th=\\[\\s*([0-9]*)\\s*\\][, ]*)?(?:([0-9.]*)th=\\[\\s*([0-9]*)\\s*\\][, ]*)?$");

        Boolean isUsec;

        String clatPercentilesLine = scanner.nextLine().trim();
        while(!clatPercentilesLine.startsWith("clat percentiles")) {
            clatPercentilesLine = scanner.nextLine().trim();

        }
        isUsec = clatPercentilesLine.contains("usec");


        TreeMap<Double,Double> percentilesMap = new TreeMap<>();
        for (int i = 0; i < 5; i++) {
            String percentiles = scanner.nextLine();
            Matcher m = p.matcher(percentiles);
            if(m.find()) {
                for (int j = 1; j < m.groupCount(); j+=2) {
                    String key = m.group(j);
                    String value = m.group(j+1);
                    if (key != null && value != null) {
                        double value2 = (isUsec) ? Integer.parseInt(value): Integer.parseInt(value)/1000.0;
                        percentilesMap.put(Double.parseDouble(key), value2);
                    }
                }
            }
        }
        job.CLATpercentiles = percentilesMap;
        return job;
    }

    private static JobInfo ExtractLAT(Scanner scanner, JobInfo job) {

        String latLine = scanner.nextLine().trim();
        while(!latLine.startsWith("lat")){
            latLine = scanner.nextLine().trim();
        }
        String unitOfMeasurement = latLine.substring(5,9);

        String[] splittedString = latLine.replaceAll("\\s+","").split(",");
        for (int i = 0; i < splittedString.length; i++) {
            if(splittedString[i].startsWith("avg")){
                String[] splitAvg = splittedString[i].split("=");
                job.LAT = splitAvg[1].substring(0, splitAvg[1].length()-1)+unitOfMeasurement;
                break;
            }
        }

        return job;
    }

    public static JobInfo ExtractBWandIOPS(Scanner scanner, JobInfo job){
        Pattern p = Pattern.compile("^(?:\\s*(?:\\w*):\\s*IOPS=([\\w.]*),\\s*BW=([\\w.\\/]*)\\s*\\(([\\w.\\/]*)\\).*)$");
        String nextLine = scanner.nextLine();
        Matcher m = p.matcher(nextLine);

        if(m.find()) {
            String iops = m.group(1);
            String bw = m.group(2);
            job.IOPS = iops;
            job.BW = bw;
        }
        return job;
    }

    public static ArrayList<JobInfo> GetJobNames(int numJobs, Scanner scanner){
        ArrayList<JobInfo> jobs = new ArrayList<>();

        for(int i=0; i<numJobs; i++){
            String currentLine = scanner.nextLine();
            if (currentLine.startsWith("...")){
                i--;
            } else {
                //job found
                String[] splittedLine = currentLine.split(":");
                JobInfo jobInfo = new JobInfo(splittedLine[0]);
                jobs.add(jobInfo);
            }

        }
        return jobs;
    }


    public static void CheckArguments(String[] args) {
        if(IsInteger(args[0]) && IsInteger(args[args.length-1])) {
            System.out.println("The first argument must be the n number of Fio files to parse");
            System.out.println("The second argument must be the n amount of input Fio files");
            System.out.println("The third argument is a single number of benchmarks in each Fio file. ");
            System.out.println("Example run: ");
            System.out.println("java FioCleaner.java 3 clat.txt flat.txt olat.txt 2");
            return;
        }
    }

    private static void PrintLatexTable(ArrayList<JobInfo> fioJobs) {
        System.out.println("\\begin{table}[H]");
        System.out.println("\\begin{tabular}{|l|l|l|l|l|}");
        System.out.println("\\hline");
        System.out.print("\\textbf{device}&");
        for (int i = 0; i < fioJobs.size(); i++) {
            if (i!=fioJobs.size()-1){
                System.out.print("\\textit{\\textbf{"+fioJobs.get(i).NAME+"}} &");
            } else {
                System.out.print("\\textit{\\textbf{"+fioJobs.get(i).NAME+"}} \\\\ \\hline \n");
            }
        }

        System.out.print("bandwidth & ");
        for (int i = 0; i < fioJobs.size(); i++) {

            if (i != fioJobs.size()-1){
                System.out.print(fioJobs.get(i).BW + " & ");
            } else {
                System.out.print(fioJobs.get(i).BW + "\\\\ \\hline \n");
            }
        }

        System.out.print("IOPS & ");
        for (int i = 0; i < fioJobs.size(); i++) {

            if (i != fioJobs.size()-1){
                System.out.print(fioJobs.get(i).IOPS + " & ");
            } else {
                System.out.print(fioJobs.get(i).IOPS + "\\\\ \\hline \n");
            }
        }

        System.out.print("latency & ");
        for (int i = 0; i < fioJobs.size(); i++) {
            if (i != fioJobs.size()-1){
                System.out.print(fioJobs.get(i).LAT + " & ");
            } else {
                System.out.print(fioJobs.get(i).LAT + "\\\\ \\hline \n");
            }
        }

        System.out.print("cpu & ");
        for (int i = 0; i < fioJobs.size(); i++) {
            if (i != fioJobs.size()-1){
                System.out.print(fioJobs.get(i).CPU + " & ");
            } else {
                System.out.print(fioJobs.get(i).CPU + "\\\\ \\hline \n");
            }
        }

        System.out.println("\\end{tabular}");
        System.out.println("\\caption{" + fioJobs.get(0).DATE +"}");
        System.out.println("\\end{table}");
    }


    public static ArrayList<JobInfo> GetFioJobs(){
        return myFioJobs;
    }

    private static boolean IsInteger(String s){
        int intValue = 0;
        try {
            intValue = Integer.parseInt(s);
            return true;
        } catch (NumberFormatException e) {
            System.out.println("Input String cannot be parsed to Integer.");
            return false;
        }
    }

}
