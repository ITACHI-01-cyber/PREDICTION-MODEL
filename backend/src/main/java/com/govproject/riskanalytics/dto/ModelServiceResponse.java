package com.govproject.riskanalytics.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ModelServiceResponse {

    @JsonProperty("cost_overrun_crore")
    private double costOverrunCrore;

    @JsonProperty("time_overrun_months")
    private int timeOverrunMonths;

    @JsonProperty("cost_overrun_percentage")
    private double costOverrunPercentage;

    @JsonProperty("time_overrun_percentage")
    private double timeOverrunPercentage;

    @JsonProperty("risk_category")
    private String riskCategory;

    @JsonProperty("risk_drivers")
    private List<RiskDriverDto> riskDrivers;

    @JsonProperty("model_version")
    private String modelVersion;

    @JsonProperty("prediction_timestamp")
    private String predictionTimestamp;

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class RiskDriverDto {
        private String feature;

        @JsonProperty("raw_value")
        private double rawValue;

        private double contribution;
    }
}
