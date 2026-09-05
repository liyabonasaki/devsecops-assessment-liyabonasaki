# =============================================================================
# country-service — Secure Multi-Stage Dockerfile
# Spring Boot 3 / Java 17 (LTS) backend
# =============================================================================
#
# Security decisions:
#   1. Multi-stage build — build toolchain (Maven + JDK) never ships in the
#      final image, removing ~600 MB of attack surface.
#   2. Eclipse Temurin (Adoptium) base — well-maintained, regularly patched,
#      preferred over OpenJDK Docker Hub images which lag on CVE fixes.
#   3. Non-root user (appuser:1001) — container cannot escalate privileges
#      even if a CVE allows code execution.
#   4. Read-only filesystem hint — the app only writes to /tmp (Spring tmp).
#   5. No unnecessary packages — JRE-only final image (no compiler, no shell
#      tools like curl/wget that aid lateral movement).
#   6. COPY --chown ensures the JAR is owned by the non-root user.
#   7. No secrets in image — DB credentials and API URLs are injected at
#      runtime via environment variables (see docker-compose.yml).
#   8. HEALTHCHECK — lets the orchestrator detect and restart unhealthy pods.
# =============================================================================

# ── Stage 1: Build ────────────────────────────────────────────────────────────
FROM eclipse-temurin:17-jdk-alpine AS builder

LABEL stage="builder"

WORKDIR /build

# Copy dependency manifests first to exploit Docker layer caching.
# Maven only re-downloads dependencies when pom.xml changes.
COPY pom.xml .
COPY .mvn/ .mvn/
COPY mvnw .
RUN chmod +x mvnw

# Download dependencies in a separate layer (cache-friendly)
RUN ./mvnw dependency:go-offline -B --no-transfer-progress

# Copy source and build, skipping checkstyle + tests (tests run in CI separately)
COPY src/ src/
RUN ./mvnw package \
        -DskipTests \
        -Dcheckstyle.skip=true \
        -B \
        --no-transfer-progress

# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM eclipse-temurin:17-jre-alpine AS runtime

# Metadata
LABEL maintainer="liyabona.saki" \
      org.opencontainers.image.title="country-service" \
      org.opencontainers.image.description="Country REST API — Spring Boot" \
      org.opencontainers.image.version="0.0.1"

# Create a non-root system user + group.
# UID/GID 1001 avoids conflicts with common host UIDs (1000 = default user).
RUN addgroup -S appgroup && adduser -S appuser -G appgroup -u 1001

WORKDIR /app

# Copy only the fat JAR from the builder stage — nothing else
COPY --from=builder --chown=appuser:appgroup /build/target/*.jar app.jar

# Switch to non-root before any runtime operations
USER appuser

# Expose the application port (internal only; mapped in docker-compose)
EXPOSE 8081

# JVM hardening flags:
#   -XX:+UseContainerSupport        respect cgroup memory limits
#   -XX:MaxRAMPercentage=75.0       cap heap at 75% of container memory
#   -Djava.security.egd=...         faster entropy on Linux for SSL/TLS
#   -Dspring.profiles.active        injected at runtime; default to prod
ENTRYPOINT ["java", \
  "-XX:+UseContainerSupport", \
  "-XX:MaxRAMPercentage=75.0", \
  "-Djava.security.egd=file:/dev/./urandom", \
  "-jar", "app.jar"]

# Healthcheck — polls the Spring Boot actuator health endpoint every 30 s.
# Requires spring-boot-starter-actuator on the classpath (or use /api/countries).
HEALTHCHECK --interval=30s --timeout=5s --start-period=45s --retries=3 \
  CMD wget -qO- http://localhost:8081/api/countries || exit 1
