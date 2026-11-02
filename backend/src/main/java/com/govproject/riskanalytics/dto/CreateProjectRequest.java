package com.govproject.riskanalytics.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Positive;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class CreateProjectRequest {

    @NotBlank(message = "Project name is required")
    private String projectName;

    @NotBlank(message = "Sector is required")
    private String sector;

    @NotBlank(message = "State is required")
    private String state;

    @Positive(message = "Original cost must be positive")
    private double originalCost;

    private double revisedCost;
    private double physicalProgress;
    private int timeDelayMonths;
    private String description;
}
