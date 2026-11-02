package com.govproject.riskanalytics.service;

import com.govproject.riskanalytics.dto.CreateProjectRequest;
import com.govproject.riskanalytics.dto.ProjectDto;
import com.govproject.riskanalytics.model.Prediction;
import com.govproject.riskanalytics.model.Project;
import com.govproject.riskanalytics.repository.PredictionRepository;
import com.govproject.riskanalytics.repository.ProjectRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class ProjectService {

    private final ProjectRepository projectRepository;
    private final PredictionRepository predictionRepository;

    public Project saveProject(Project project) {
        return projectRepository.save(project);
    }

    public ProjectDto createProject(CreateProjectRequest request) {
        Project project = Project.builder()
                .projectName(request.getProjectName())
                .sector(request.getSector())
                .state(request.getState())
                .originalCost(request.getOriginalCost())
                .revisedCost(request.getRevisedCost())
                .physicalProgress(request.getPhysicalProgress())
                .timeDelayMonths(request.getTimeDelayMonths())
                .description(request.getDescription())
                .createdAt(Instant.now())
                .updatedAt(Instant.now())
                .build();
        Project saved = projectRepository.save(project);
        return mapToDto(saved);
    }

    public ProjectDto getProjectById(String id) {
        Project p = projectRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Project not found: " + id));
        return mapToDto(p);
    }

    public List<Project> getAllProjects() {
        return projectRepository.findAll();
    }

    public List<Project> searchProjects(String search) {
        return projectRepository.findBySectorContainingIgnoreCase(search);
    }

    public List<Prediction> getProjectPredictions(String projectId) {
        return predictionRepository.findByProjectId(projectId);
    }

    public ProjectDto updateProject(String id, Map<String, Object> updates) {
        Project p = projectRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Project not found: " + id));

        if (updates.containsKey("projectName")) {
            p.setProjectName((String) updates.get("projectName"));
        }
        if (updates.containsKey("sector")) {
            p.setSector((String) updates.get("sector"));
        }
        if (updates.containsKey("state")) {
            p.setState((String) updates.get("state"));
        }
        if (updates.containsKey("originalCost")) {
            p.setOriginalCost(Double.parseDouble(updates.get("originalCost").toString()));
        }
        if (updates.containsKey("physicalProgress")) {
            p.setPhysicalProgress(Double.parseDouble(updates.get("physicalProgress").toString()));
        }
        if (updates.containsKey("timeDelayMonths")) {
            p.setTimeDelayMonths(Integer.parseInt(updates.get("timeDelayMonths").toString()));
        }
        p.setUpdatedAt(Instant.now());
        Project saved = projectRepository.save(p);
        return mapToDto(saved);
    }

    public ProjectDto mapToDto(Project p) {
        return ProjectDto.builder()
                .id(p.getId())
                .projectName(p.getProjectName())
                .sector(p.getSector())
                .state(p.getState())
                .originalCost(p.getOriginalCost())
                .revisedCost(p.getRevisedCost())
                .physicalProgress(p.getPhysicalProgress())
                .timeDelayMonths(p.getTimeDelayMonths())
                .description(p.getDescription())
                .createdBy(p.getCreatedBy())
                .createdAt(p.getCreatedAt())
                .updatedAt(p.getUpdatedAt())
                .build();
    }
}
