package com.govproject.riskanalytics.controller;

import com.govproject.riskanalytics.dto.CreateProjectRequest;
import com.govproject.riskanalytics.dto.ProjectDto;
import com.govproject.riskanalytics.service.ProjectService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Slf4j
@RestController
@RequestMapping("/api/projects")
@RequiredArgsConstructor
public class ProjectController {

    private final ProjectService projectService;

    @PostMapping
    public ResponseEntity<?> createProject(@RequestBody CreateProjectRequest request) {
        try {
            ProjectDto projectDto = projectService.createProject(request);
            return ResponseEntity.ok(projectDto);
        } catch (Exception e) {
            Map<String, Object> response = new HashMap<>();
            response.put("error", "Failed to create project");
            response.put("message", e.getMessage());
            return ResponseEntity.badRequest().body(response);
        }
    }

    @GetMapping
    public ResponseEntity<?> getProjects(@RequestParam(defaultValue = "0") int page,
                                        @RequestParam(defaultValue = "10") int size,
                                        @RequestParam(required = false) String search) {
        List<ProjectDto> projects;

        if (search != null && !search.isEmpty()) {
            projects = projectService.searchProjects(search).stream()
                    .map(this::mapToDto)
                    .collect(Collectors.toList());
        } else {
            projects = projectService.getAllProjects().stream()
                    .map(this::mapToDto)
                    .collect(Collectors.toList());
        }

        Map<String, Object> response = new HashMap<>();
        response.put("projects", projects);
        response.put("page", page);
        response.put("size", size);
        response.put("total", projects.size());
        return ResponseEntity.ok(response);
    }

    @GetMapping("/{id}")
    public ResponseEntity<?> getProjectById(@PathVariable String id) {
        try {
            ProjectDto projectDto = projectService.getProjectById(id);
            return ResponseEntity.ok(projectDto);
        } catch (Exception e) {
            Map<String, Object> response = new HashMap<>();
            response.put("error", "Project not found");
            response.put("message", id);
            return ResponseEntity.notFound().build();
        }
    }

    @GetMapping("/predict/{id}")
    public ResponseEntity<?> getPredictionsForProject(@PathVariable String id) {
        try {
            return ResponseEntity.ok(projectService.getProjectPredictions(id));
        } catch (Exception e) {
            return ResponseEntity.notFound().build();
        }
    }

    @PutMapping("/{id}")
    public ResponseEntity<?> updateProject(@PathVariable String id, @RequestBody Map<String, Object> updates) {
        try {
            ProjectDto projectDto = projectService.updateProject(id, updates);
            return ResponseEntity.ok(projectDto);
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }

    @PreAuthorize("hasRole('ADMIN')")
    @GetMapping("/admin")
    public ResponseEntity<?> getAllProjectsAdmin() {
        List<ProjectDto> projects = projectService.getAllProjects().stream()
                .map(this::mapToDto)
                .collect(Collectors.toList());
        return ResponseEntity.ok(projects);
    }

    private ProjectDto mapToDto(com.govproject.riskanalytics.model.Project project) {
        return ProjectDto.builder()
                .id(project.getId())
                .projectName(project.getProjectName())
                .sector(project.getSector())
                .state(project.getState())
                .originalCost(project.getOriginalCost())
                .revisedCost(project.getRevisedCost())
                .physicalProgress(project.getPhysicalProgress())
                .timeDelayMonths(project.getTimeDelayMonths())
                .description(project.getDescription())
                .createdBy(project.getCreatedBy())
                .createdAt(project.getCreatedAt())
                .updatedAt(project.getUpdatedAt())
                .build();
    }
}