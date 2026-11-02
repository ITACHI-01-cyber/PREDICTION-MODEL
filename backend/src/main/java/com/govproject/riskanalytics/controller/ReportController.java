package com.govproject.riskanalytics.controller;

import com.govproject.riskanalytics.model.Prediction;
import com.govproject.riskanalytics.service.PredictionService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.nio.charset.StandardCharsets;
import java.util.List;

@RestController
@RequestMapping("/api/reports")
@RequiredArgsConstructor
public class ReportController {

    private final PredictionService predictionService;

    @GetMapping("/export/csv")
    public ResponseEntity<byte[]> exportCSV() {
        List<Prediction> predictions = predictionService.getAllPredictions(0, 1000);

        StringBuilder csv = new StringBuilder();
        csv.append("Prediction_ID,Project_Name,Sector,Original_Cost_Cr,Physical_Progress_Pct,Time_Delay_Months,")
           .append("Cost_Overrun_Cr,Time_Overrun_Months,Cost_Overrun_Pct,Risk_Category,Officer_Name,Created_At\n");

        for (Prediction p : predictions) {
            String projName = (p.getInputSnapshot() != null && p.getInputSnapshot().getSector() != null)
                    ? p.getInputSnapshot().getSector() : "N/A";
            double origCost = p.getInputSnapshot() != null ? p.getInputSnapshot().getOriginalCost() : 0.0;
            double progress = p.getInputSnapshot() != null ? p.getInputSnapshot().getPhysicalProgress() : 0.0;
            int delay = p.getInputSnapshot() != null ? p.getInputSnapshot().getTimeDelayMonths() : 0;

            csv.append(escape(p.getId())).append(",")
               .append(escape(projName)).append(",")
               .append(escape(projName)).append(",")
               .append(origCost).append(",")
               .append(progress).append(",")
               .append(delay).append(",")
               .append(p.getCostOverrunCrore()).append(",")
               .append(p.getTimeOverrunMonths()).append(",")
               .append(p.getCostOverrunPercentage()).append(",")
               .append(p.getRiskCategory() != null ? p.getRiskCategory().name() : "MODERATE").append(",")
               .append(escape(p.getOfficerName())).append(",")
               .append(p.getCreatedAt() != null ? p.getCreatedAt().toString() : "").append("\n");
        }

        byte[] output = csv.toString().getBytes(StandardCharsets.UTF_8);

        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"govproject_risk_export.csv\"")
                .contentType(MediaType.parseMediaType("text/csv"))
                .body(output);
    }

    private String escape(String val) {
        if (val == null) return "\"\"";
        return "\"" + val.replace("\"", "\"\"") + "\"";
    }
}

