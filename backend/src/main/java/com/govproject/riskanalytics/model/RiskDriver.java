package com.govproject.riskanalytics.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RiskDriver {

    private String feature;
    private double rawValue;
    private double contribution;
}
