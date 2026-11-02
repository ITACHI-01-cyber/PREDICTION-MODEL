package com.govproject.riskanalytics.repository;

import com.govproject.riskanalytics.model.Project;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface ProjectRepository extends MongoRepository<Project, String> {

    long count();

    List<Project> findBySectorContainingIgnoreCase(String sector);

    List<Project> findByCreatedBy(String createdBy);

    List<Project> findBySectorContainingIgnoreCase(String sector, Pageable pageable);
    Page<Project> findByCreatedBy(String createdBy, Pageable pageable);
}
