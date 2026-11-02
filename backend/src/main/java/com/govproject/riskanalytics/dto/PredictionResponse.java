package com.govproject.riskanalytics.dto;

import com.govproject.riskanalytics.model.PredictionInput;
import com.govproject.riskanalytics.model.RiskDriver;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;
import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class PredictionResponse {

    private String id;
    private String projectId;
    private String officerId;
    private String officerName;
    private PredictionInput inputSnapshot;
    private double costOverrunCrore;
    private int timeOverrunMonths;
    private double costOverrunPercentage;
    private double timeOverrunPercentage;
    private String riskCategory;
    private List<RiskDriver> riskDrivers;
    private String modelVersion;
    private Instant createdAt;
    private String status;
}
