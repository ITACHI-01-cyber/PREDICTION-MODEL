package com.govproject.riskanalytics.service;

import com.govproject.riskanalytics.dto.ModelServiceRequest;
import com.govproject.riskanalytics.dto.ModelServiceResponse;
import com.govproject.riskanalytics.dto.PredictionRequest;
import com.govproject.riskanalytics.dto.PredictionResponse;
import com.govproject.riskanalytics.model.Prediction;
import com.govproject.riskanalytics.model.PredictionInput;
import com.govproject.riskanalytics.model.RiskDriver;
import com.govproject.riskanalytics.repository.PredictionRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class PredictionService {

    private final PredictionRepository predictionRepository;
    private final RestTemplate restTemplate = new RestTemplate();

    @Value("${model.service.url:http://localhost:8000}")
    private String modelServiceUrl;

    public PredictionResponse createPrediction(PredictionRequest request, String officerId, String officerName) {
        log.info("Executing prediction for sector: {}, cost: {}", request.getSector(), request.getOriginalCost());

        ModelServiceRequest modelReq = ModelServiceRequest.builder()
                .sector(request.getSector())
                .originalCost(request.getOriginalCost())
                .physicalProgress(request.getPhysicalProgress())
                .timeDelayMonths(request.getTimeDelayMonths())
                .build();

        ModelServiceResponse modelResp;
        try {
            org.springframework.http.HttpHeaders headers = new org.springframework.http.HttpHeaders();
            headers.setContentType(org.springframework.http.MediaType.APPLICATION_JSON);
            org.springframework.http.HttpEntity<ModelServiceRequest> entity = new org.springframework.http.HttpEntity<>(modelReq, headers);
            ResponseEntity<ModelServiceResponse> response = restTemplate.postForEntity(
                    modelServiceUrl + "/predict",
                    entity,
                    ModelServiceResponse.class
            );
            modelResp = response.getBody();
        } catch (Exception e) {
            log.error("Failed to call ML model service at {}: {}", modelServiceUrl, e.getMessage());
            throw new RuntimeException("Model prediction service unreachable: " + e.getMessage());
        }

        if (modelResp == null) {
            throw new RuntimeException("Empty response from ML model service");
        }

        PredictionInput inputSnapshot = PredictionInput.builder()
                .sector(request.getSector())
                .originalCost(request.getOriginalCost())
                .physicalProgress(request.getPhysicalProgress())
                .timeDelayMonths(request.getTimeDelayMonths())
                .build();

        List<RiskDriver> riskDrivers = Collections.emptyList();
        if (modelResp.getRiskDrivers() != null) {
            riskDrivers = modelResp.getRiskDrivers().stream()
                    .map(d -> RiskDriver.builder()
                            .feature(d.getFeature())
                            .rawValue(d.getRawValue())
                            .contribution(d.getContribution())
                            .build())
                    .collect(Collectors.toList());
        }

        Prediction.RiskCategory riskCategory;
        try {
            riskCategory = Prediction.RiskCategory.valueOf(modelResp.getRiskCategory().toUpperCase());
        } catch (Exception e) {
            riskCategory = Prediction.RiskCategory.MODERATE;
        }

        Prediction prediction = Prediction.builder()
                .projectId(request.getProjectId())
                .officerId(officerId)
                .officerName(officerName)
                .inputSnapshot(inputSnapshot)
                .costOverrunCrore(modelResp.getCostOverrunCrore())
                .timeOverrunMonths(modelResp.getTimeOverrunMonths())
                .costOverrunPercentage(modelResp.getCostOverrunPercentage())
                .timeOverrunPercentage(modelResp.getTimeOverrunPercentage())
                .riskCategory(riskCategory)
                .riskDrivers(riskDrivers)
                .modelVersion(modelResp.getModelVersion() != null ? modelResp.getModelVersion() : "1.0.0")
                .createdAt(Instant.now())
                .status("COMPLETED")
                .build();

        Prediction saved = predictionRepository.save(prediction);
        log.info("Saved prediction record: {}", saved.getId());

        return mapToResponse(saved);
    }

    public List<Prediction> getAllPredictions(int page, int size) {
        Page<Prediction> paged = predictionRepository.findAll(
                PageRequest.of(page, size, Sort.by(Sort.Direction.DESC, "createdAt"))
        );
        return paged.getContent();
    }

    public PredictionResponse getPredictionById(String id) {
        Prediction p = predictionRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Prediction not found: " + id));
        return mapToResponse(p);
    }

    public List<Prediction> getPredictionsByProject(String projectId) {
        return predictionRepository.findByProjectId(projectId);
    }

    public PredictionResponse mapToResponse(Prediction p) {
        return PredictionResponse.builder()
                .id(p.getId())
                .projectId(p.getProjectId())
                .officerId(p.getOfficerId())
                .officerName(p.getOfficerName())
                .inputSnapshot(p.getInputSnapshot())
                .costOverrunCrore(p.getCostOverrunCrore())
                .timeOverrunMonths(p.getTimeOverrunMonths())
                .costOverrunPercentage(p.getCostOverrunPercentage())
                .timeOverrunPercentage(p.getTimeOverrunPercentage())
                .riskCategory(p.getRiskCategory() != null ? p.getRiskCategory().name() : "MODERATE")
                .riskDrivers(p.getRiskDrivers())
                .modelVersion(p.getModelVersion())
                .createdAt(p.getCreatedAt())
                .status(p.getStatus())
                .build();
    }
}

