import javafx.application.Application;
import javafx.application.Platform;
import javafx.embed.swing.SwingFXUtils;
import javafx.event.ActionEvent;
import javafx.fxml.FXML;
import javafx.scene.Scene;
import javafx.scene.chart.BarChart;
import javafx.scene.chart.CategoryAxis;
import javafx.scene.chart.NumberAxis;
import javafx.scene.chart.XYChart;
import javafx.scene.image.WritableImage;
import javafx.stage.Stage;

import javax.imageio.ImageIO;
import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Map;
import java.util.TreeMap;

public class BarChartTogether extends Application {

    @Override
    public void start(Stage stage) {

        ArrayList<JobInfo> fioJobs = FioCleaner.GetFioJobs();

        ArrayList<XYChart.Series> series = fetchSeries(fioJobs);

        stage.setTitle("CLat percentile distribution");
        final CategoryAxis xAxis = new CategoryAxis();
        final NumberAxis yAxis = new NumberAxis();
        xAxis.setLabel("CLat percentiles");
        yAxis.setLabel("latency in usec");

        final BarChart<String, Number> bc =
                new BarChart<String, Number>(xAxis, yAxis);

        bc.setAnimated(false);

        for (XYChart.Series serie : series){
            bc.getData().addAll(serie);
        }
        bc.setTitle("CLat percentile distribution");

        Scene scene = new Scene(bc, 800, 600);

        //stage.setScene(scene);
        //stage.show();

        bc.applyCss();
        bc.layout();

        //Save the scene as PNG image
        WritableImage image = scene.snapshot(null);
        String filepath = System.getProperty("user.dir");
        String jobdate = fioJobs.get(0).DATE.trim();
        jobdate = jobdate.replaceAll(" ", "-");
        jobdate = jobdate.replaceAll(":", ";");
        String filename = filepath + "\\" + "clat-percentiles" +  "-" + jobdate + ".png";
        File file = new File(filename);
        try {
            ImageIO.write(SwingFXUtils.fromFXImage(image, null), "PNG", file);
            System.out.println("PNG-image saved at path: " + filename);
        } catch (IOException e) {
            e.printStackTrace();
        }

        exitApplication(null);

    }

    public static void main(String args[]){
        launch(args);
    }

    public ArrayList<XYChart.Series> fetchSeries(ArrayList<JobInfo> fioJobs){
        ArrayList<XYChart.Series> result = new ArrayList<>();
        for (int i = 0; i < fioJobs.size(); i++) {
            TreeMap<Double, Double> clatPercentiles = fioJobs.get(i).CLATpercentiles;

            XYChart.Series currentSeries = new XYChart.Series();
            currentSeries.setName(fioJobs.get(i).NAME);

            for(Map.Entry<Double, Double> entry : clatPercentiles.entrySet()) {
                double key = entry.getKey();
                double value = entry.getValue();
                currentSeries.getData().add(new XYChart.Data(key+"%", value));
            }
            result.add(currentSeries);
        }
        return result;
    }

    @FXML
    public void exitApplication(ActionEvent event) {
        Platform.exit();
    }

}