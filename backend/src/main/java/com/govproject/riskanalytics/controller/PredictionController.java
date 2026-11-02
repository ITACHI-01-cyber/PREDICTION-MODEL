package com.govproject.riskanalytics.controller;

import com.govproject.riskanalytics.dto.PredictionRequest;
import com.govproject.riskanalytics.dto.PredictionResponse;
import com.govproject.riskanalytics.model.User;
import com.govproject.riskanalytics.service.AuthService;
import com.govproject.riskanalytics.service.PredictionService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/predictions")
@RequiredArgsConstructor
public class PredictionController {

    private final PredictionService predictionService;
    private final AuthService authService;

    @PostMapping
    public ResponseEntity<?> createPrediction(@Valid @RequestBody PredictionRequest request,
                                               @RequestHeader(value = "Authorization", required = false) String authHeader) {
        try {
            String officerId = "system-officer";
            String officerName = "Project Officer";
            if (authHeader != null && authHeader.startsWith("Bearer ")) {
                String token = authHeader.substring(7);
                try {
                    User user = authService.getCurrentUser(token);
                    officerId = user.getId() != null ? user.getId() : user.getUsername();
                    officerName = user.getFullName() != null ? user.getFullName() : user.getUsername();
                } catch (Exception ignored) {
                }
            }

            PredictionResponse response = predictionService.createPrediction(request, officerId, officerName);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            Map<String, Object> response = new HashMap<>();
            response.put("error", "Prediction failed");
            response.put("message", e.getMessage());
            return ResponseEntity.internalServerError().body(response);
        }
    }

    @GetMapping
    public ResponseEntity<?> getPredictions(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size) {
        List<PredictionResponse> predictions = predictionService.getAllPredictions(page, size)
                .stream()
                .map(predictionService::mapToResponse)
                .toList();

        Map<String, Object> response = new HashMap<>();
        response.put("predictions", predictions);
        response.put("page", page);
        response.put("size", size);
        response.put("total", predictions.size());
        return ResponseEntity.ok(response);
    }

    @GetMapping("/{id}")
    public ResponseEntity<?> getPredictionById(@PathVariable String id) {
        try {
            PredictionResponse resp = predictionService.getPredictionById(id);
            return ResponseEntity.ok(resp);
        } catch (Exception e) {
            return ResponseEntity.notFound().build();
        }
    }

    @GetMapping("/project/{projectId}")
    public ResponseEntity<?> getPredictionsByProject(@PathVariable String projectId) {
        List<PredictionResponse> predictions = predictionService.getPredictionsByProject(projectId)
                .stream()
                .map(predictionService::mapToResponse)
                .toList();

        Map<String, Object> response = new HashMap<>();
        response.put("predictions", predictions);
        response.put("total", predictions.size());
        return ResponseEntity.ok(response);
    }
}
