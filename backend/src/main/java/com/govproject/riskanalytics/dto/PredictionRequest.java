package com.govproject.riskanalytics.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Positive;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class PredictionRequest {

    @NotBlank(message = "Sector is required")
    private String sector;

    @Positive(message = "Original cost must be positive")
    private double originalCost;

    @Min(value = 0, message = "Physical progress cannot be negative")
    @Max(value = 100, message = "Physical progress cannot exceed 100")
    private double physicalProgress;

    @Min(value = 0, message = "Time delay cannot be negative")
    private int timeDelayMonths;

    private String projectId;
}
