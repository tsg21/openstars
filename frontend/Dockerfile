# --- Build stage ---
FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# --- Serve stage ---
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

# BACKEND_URL is resolved at container start by nginx's envsubst.
# nginx:alpine auto-processes /etc/nginx/templates/*.template files,
# substituting environment variables, and writes the result to
# /etc/nginx/conf.d/ before starting nginx.
#
# Example: BACKEND_URL=http://backend:8080
ENV BACKEND_URL=http://localhost:8080

EXPOSE 8080
