package com.govproject.riskanalytics;

import com.govproject.riskanalytics.service.AuthService;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;

@SpringBootApplication
public class GovProjectApplication {

    public static void main(String[] args) {
        SpringApplication.run(GovProjectApplication.class, args);
    }

    @Bean
    public CommandLineRunner init(AuthService authService) {
        return args -> {
            authService.createBootstrapUserIfNeeded();
        };
    }
}
