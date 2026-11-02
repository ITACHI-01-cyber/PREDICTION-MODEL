package com.govproject.riskanalytics.repository;

import com.govproject.riskanalytics.model.Prediction;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface PredictionRepository extends MongoRepository<Prediction, String> {

    List<Prediction> findByProjectId(String projectId);
List<Prediction> findTop10ByOrderByCreatedAtDesc();

    Page<Prediction> findByOfficerId(String officerId, Pageable pageable);

    long countByRiskCategory(Prediction.RiskCategory riskCategory);
}
