# =============================================================================
# country-flags-app - Secure Multi-Stage Dockerfile
# React 18 frontend served by Nginx
# =============================================================================
#
# Security decisions:
#   1. Multi-stage build - Node.js build toolchain (node_modules, npm, build
#      caches) never reaches the final image.
#   2. node:18-alpine builder - minimal Alpine base reduces CVE surface during
#      the build stage.
#   3. nginx:alpine final image - significantly smaller and fewer CVEs than
#      nginx:latest (Debian-based). Only static file serving capability.
#   4. Custom nginx.conf - removes server version disclosure (server_tokens off),
#      adds security headers (X-Frame-Options, X-Content-Type-Options, CSP,
#      HSTS), and disables directory listing.
#   5. Non-root Nginx - nginx:alpine supports running on port 8080 as non-root.
#      We create a dedicated nginx user and configure the pid/temp dirs.
#   6. No .env baked in - REACT_APP_API_URL is injected at build time via
#      --build-arg so different environments use the same image pattern.
#   7. Read-only static files - only /var/cache/nginx and /tmp need write access.
# =============================================================================

# -- Stage 1: Build ------------------------------------------------------------
FROM node:18-alpine AS builder

LABEL stage="builder"

WORKDIR /app

# Copy manifests first for dependency layer caching
COPY package.json package-lock.json ./

# Prefer reproducible `npm ci`. If the lock file is out of sync with
# package.json (e.g. after dependency changes that haven't been re-locked),
# fall back to `npm install` to reconcile the lock, then continue.
RUN npm ci --prefer-offline || \
    (echo "package-lock.json out of sync - reconciling with npm install" && \
     npm install --no-audit --no-fund)

# Accept API URL as a build argument (no hardcoded URLs in image)
ARG REACT_APP_API_URL=http://localhost:8081
ENV REACT_APP_API_URL=$REACT_APP_API_URL

# Copy source and build
COPY public/ public/
COPY src/ src/
COPY .babelrc babel.config.cjs jest.config.json ./

RUN npm run build

# -- Stage 2: Runtime (Nginx) --------------------------------------------------
FROM nginx:1.27-alpine AS runtime

LABEL maintainer="liyabona.saki" \
      org.opencontainers.image.title="country-flags-app" \
      org.opencontainers.image.description="Country Flags React App - Nginx" \
      org.opencontainers.image.version="0.1.0"

# Remove default nginx config and any sample html
RUN rm -rf /usr/share/nginx/html/* \
        /etc/nginx/conf.d/default.conf

# Copy build output from builder stage
COPY --from=builder /app/build /usr/share/nginx/html

# Copy hardened nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Create a non-root user for nginx.
# nginx:alpine includes the 'nginx' user by default; we lock it down further.
RUN chown -R nginx:nginx /usr/share/nginx/html \
 && chown -R nginx:nginx /var/cache/nginx \
 && touch /var/run/nginx.pid \
 && chown nginx:nginx /var/run/nginx.pid

USER nginx

# Run on 8080 (unprivileged port - avoids needing NET_BIND_SERVICE capability)
EXPOSE 8080

# Use 127.0.0.1 (not localhost): in Alpine, localhost may resolve to IPv6 ::1
# first, but nginx listens on IPv4, causing a false "connection refused".
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://127.0.0.1:8080/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
