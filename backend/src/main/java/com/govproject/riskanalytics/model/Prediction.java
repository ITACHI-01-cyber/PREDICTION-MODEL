package com.govproject.riskanalytics.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.Instant;
import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Document(collection = "predictions")
public class Prediction {

    @Id
    private String id;

    @Indexed
    private String projectId;

    @Indexed
    private String officerId;

    private String officerName;
    private PredictionInput inputSnapshot;
    private double costOverrunCrore;
    private int timeOverrunMonths;
    private double costOverrunPercentage;
    private double timeOverrunPercentage;
    private RiskCategory riskCategory;
    private List<RiskDriver> riskDrivers;
    private String modelVersion;

    @CreatedDate
    private Instant createdAt;

    @Builder.Default
    private String status = "COMPLETED";

    public enum RiskCategory {
        SAFE, MODERATE, RISKY
    }
}
