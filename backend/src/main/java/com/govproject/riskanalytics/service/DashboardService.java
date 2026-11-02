package com.govproject.riskanalytics.service;

import com.govproject.riskanalytics.model.Prediction;
import com.govproject.riskanalytics.model.Project;
import com.govproject.riskanalytics.repository.PredictionRepository;
import com.govproject.riskanalytics.repository.ProjectRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Slf4j
@Service
@RequiredArgsConstructor
public class DashboardService {

    private final PredictionRepository predictionRepository;
    private final ProjectRepository projectRepository;

    public Map<String, Object> getDashboardSummary() {
        int totalProjects = (int) projectRepository.count();
        int totalPredictions = (int) predictionRepository.count();
        int totalUsers = (int) projectRepository.count(); // Will be updated when UserService is connected

        // Risk distribution
        int safeCount = (int) predictionRepository.countByRiskCategory(Prediction.RiskCategory.SAFE);
        int moderateCount = (int) predictionRepository.countByRiskCategory(Prediction.RiskCategory.MODERATE);
        int riskyCount = (int) predictionRepository.countByRiskCategory(Prediction.RiskCategory.RISKY);

        // Recent predictions
        List<Prediction> recentPredictions = predictionRepository.findTop10ByOrderByCreatedAtDesc();

        // Project distribution by sector
        Map<String, Integer> sectorDistribution = new HashMap<>();
        List<Project> allProjects = projectRepository.findAll();
        for (Project p : allProjects) {
            sectorDistribution.merge(p.getSector(), 1, Integer::sum);
        }

        Map<String, Object> summary = new HashMap<>();
        summary.put("totalProjects", totalProjects);
        summary.put("totalPredictions", totalPredictions);
        summary.put("totalUsers", totalUsers);
        summary.put("unsafePredictions", moderateCount + riskyCount);
        summary.put("riskDistribution", Map.of(
                "safe", safeCount,
                "moderate", moderateCount,
                "risky", riskyCount
        ));
        summary.put("recentPredictions", recentPredictions);
        summary.put("sectorDistribution", sectorDistribution);
        summary.put("generatedAt", LocalDateTime.now());

        return summary;
    }

    public Map<String, Object> getAnalytics() {
        List<Prediction> allPredictions = predictionRepository.findAll();
        double avgCostOverrun = allPredictions.stream()
                .mapToDouble(Prediction::getCostOverrunCrore)
                .average()
                .orElse(0.0);
        
        double avgTimeOverrun = allPredictions.stream()
                .mapToInt(Prediction::getTimeOverrunMonths)
                .average()
                .orElse(0.0);

        Map<String, Object> analytics = new HashMap<>();
        analytics.put("averageCostOverrunCrore", avgCostOverrun);
        analytics.put("averageTimeOverrunMonths", avgTimeOverrun);
        analytics.put("totalPredictions", allPredictions.size());
        return analytics;
    }
}