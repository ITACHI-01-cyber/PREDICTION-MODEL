package com.govproject.riskanalytics.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Map;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DashboardSummary {

    private long totalProjects;
    private long highRiskCount;
    private double avgCostOverrun;
    private double avgTimeOverrun;
    private Map<String, Long> riskDistribution;
}
