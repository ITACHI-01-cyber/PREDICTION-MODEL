package com.govproject.riskanalytics.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.govproject.riskanalytics.dto.LoginRequest;
import com.govproject.riskanalytics.dto.LoginResponse;
import com.govproject.riskanalytics.model.User;
import com.govproject.riskanalytics.repository.UserRepository;
import com.govproject.riskanalytics.security.JwtTokenProvider;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

@Slf4j
@Service
@RequiredArgsConstructor
public class AuthService {

    private final JwtTokenProvider jwtTokenProvider;
    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Transactional(readOnly = true)
    public LoginResponse login(LoginRequest request) {
        Optional<User> userOpt = userRepository.findByUsername(request.getUsername());
        
        if (userOpt.isEmpty()) {
            throw new RuntimeException("Invalid username or password");
        }
        
        User user = userOpt.get();
        
        if (!passwordEncoder.matches(request.getPassword(), user.getPasswordHash())) {
            throw new RuntimeException("Invalid username or password");
        }
        
        if (!user.isActive()) {
            throw new RuntimeException("User account is disabled");
        }

        String token = jwtTokenProvider.generateToken(user.getUsername(), user.getRole().name());

        return LoginResponse.builder()
                .token(token)
                .username(user.getUsername())
                .fullName(user.getFullName())
                .role(user.getRole().name())
                .build();
    }

    public String createBootstrapUserIfNeeded() {
        Optional<User> adminOpt = userRepository.findByUsername("admin");
        if (adminOpt.isPresent()) {
            return adminOpt.get().getUsername();
        }

        log.info("Creating bootstrap admin user");
        User admin = User.builder()
                .username("admin")
                .fullName("System Administrator")
                .email("admin@govproject.local")
                .passwordHash(passwordEncoder.encode("admin123"))
                .role(User.Role.ADMIN)
                .active(true)
                .build();

        User saved = userRepository.save(admin);
        log.info("Bootstrap admin user created: {}", saved.getUsername());
        return saved.getUsername();
    }

    public User getCurrentUser(String token) {
        String username = jwtTokenProvider.getUsernameFromToken(token);
        Optional<User> userOpt = userRepository.findByUsername(username);
        
        if (userOpt.isEmpty()) {
            throw new RuntimeException("User not found");
        }
        
        return userOpt.get();
    }
}