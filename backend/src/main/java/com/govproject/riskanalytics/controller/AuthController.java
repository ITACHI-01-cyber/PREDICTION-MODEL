package com.govproject.riskanalytics.controller;

import com.govproject.riskanalytics.dto.LoginRequest;
import com.govproject.riskanalytics.dto.LoginResponse;
import com.govproject.riskanalytics.service.AuthService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;

    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody LoginRequest request) {
        try {
            LoginResponse response = authService.login(request);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            Map<String, Object> response = new HashMap<>();
            response.put("error", "Authentication failed");
            response.put("message", "Invalid username or password");
            return ResponseEntity.status(401).body(response);
        }
    }

    @GetMapping("/me")
    public ResponseEntity<?> getCurrentUser(@RequestHeader("Authorization") String authHeader) {
        try {
            String token = authHeader.replace("Bearer ", "");
            String username = authService.getCurrentUser(token).getUsername();
            return ResponseEntity.ok(Map.of(
                    "username", username,
                    "fullName", authService.getCurrentUser(token).getFullName(),
                    "email", authService.getCurrentUser(token).getEmail(),
                    "role", authService.getCurrentUser(token).getRole().name()
            ));
        } catch (Exception e) {
            return ResponseEntity.status(401).body(null);
        }
    }
}