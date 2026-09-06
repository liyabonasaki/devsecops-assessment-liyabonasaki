package org.bongz.countryservice.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.web.SecurityFilterChain;

/**
 * Security configuration for the Country API.
 *
 * The project includes spring-boot-starter-security, which by default locks down
 * every endpoint and returns 401 for all requests. The provided source did not
 * include a SecurityFilterChain, so the public country API was unreachable.
 *
 * This configuration exposes the read-only country API and the API documentation
 * as public endpoints (the service holds only public country data), while keeping
 * Spring Security active for defence-in-depth (CSRF handling, security headers,
 * and a foundation for adding authentication in a later phase).
 */
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            // Stateless REST API: no server-side session, so CSRF protection
            // (which targets browser session cookies) is not applicable.
            .csrf(csrf -> csrf.disable())
            .sessionManagement(sm -> sm.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(auth -> auth
                // Public read-only country API
                .requestMatchers("/api/countries/**").permitAll()
                // API documentation (springdoc / swagger-ui)
                .requestMatchers(
                    "/v3/api-docs/**",
                    "/swagger-ui/**",
                    "/swagger-ui.html",
                    "/custom-swagger-ui.html"
                ).permitAll()
                // H2 console (dev only; disabled by default via properties)
                .requestMatchers("/h2-console/**").permitAll()
                // Everything else requires authentication
                .anyRequest().authenticated()
            )
            // Allow the H2 console to render in a frame when enabled in dev
            .headers(headers -> headers.frameOptions(frame -> frame.sameOrigin()));

        return http.build();
    }
}
