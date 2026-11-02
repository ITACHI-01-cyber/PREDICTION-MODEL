package com.govproject.riskanalytics.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ModelServiceRequest {

    private String sector;

    @JsonProperty("original_cost")
    private double originalCost;

    @JsonProperty("physical_progress")
    private double physicalProgress;

    @JsonProperty("time_delay_months")
    private int timeDelayMonths;
}
