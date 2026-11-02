package com.govproject.riskanalytics.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ProjectDto {

    private String id;
    private String projectName;
    private String sector;
    private String state;
    private double originalCost;
    private double revisedCost;
    private double physicalProgress;
    private int timeDelayMonths;
    private String description;
    private String createdBy;
    private Instant createdAt;
    private Instant updatedAt;
}
