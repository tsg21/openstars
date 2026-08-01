# --- Build stage ---
FROM node:24-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .

# Baked into the JS bundle by Vite at build time — must be set here, not at
# container runtime.
ARG VITE_FIREBASE_API_KEY
ARG VITE_FIREBASE_PROJECT_ID
ARG VITE_FIREBASE_AUTH_DOMAIN
ENV VITE_FIREBASE_API_KEY=$VITE_FIREBASE_API_KEY
ENV VITE_FIREBASE_PROJECT_ID=$VITE_FIREBASE_PROJECT_ID
ENV VITE_FIREBASE_AUTH_DOMAIN=$VITE_FIREBASE_AUTH_DOMAIN

RUN npm run build

# --- Serve stage ---
FROM caddy:2-alpine

COPY --from=build /app/dist /usr/share/caddy
COPY Caddyfile /etc/caddy/Caddyfile

# BACKEND_URL is resolved by Caddy from environment variables.
# Example: BACKEND_URL=http://backend:8080
ENV BACKEND_URL=http://undefined:8080

EXPOSE 8080
