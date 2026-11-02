package com.govproject.riskanalytics.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class PredictionInput {

    private String sector;
    private double originalCost;
    private double physicalProgress;
    private int timeDelayMonths;
}
