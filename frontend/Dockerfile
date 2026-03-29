# --- Build stage ---
FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# --- Serve stage ---
FROM caddy:2-alpine

COPY --from=build /app/dist /usr/share/caddy
COPY Caddyfile /etc/caddy/Caddyfile

# BACKEND_URL is resolved by Caddy from environment variables.
# Example: BACKEND_URL=http://backend:8080
ENV BACKEND_URL=http://localhost:8080

EXPOSE 8080
