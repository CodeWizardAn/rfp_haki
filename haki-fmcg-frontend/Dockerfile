# =============================================================================
# Enterprise Frontend Dockerfile - Haki FMCG 2.0 / Haki Procure AI
# Multi-stage Vite + React build served via hardened Nginx Alpine
# =============================================================================

# Stage 1: Build Application
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Build production bundle
RUN npm run build

# Stage 2: Serve via Nginx
FROM nginx:1.25-alpine AS runtime

COPY --from=builder /app/dist /usr/share/nginx/html
COPY ../nginx/nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -q -O - http://localhost/healthz || exit 1

CMD ["nginx", "-g", "daemon off;"]
