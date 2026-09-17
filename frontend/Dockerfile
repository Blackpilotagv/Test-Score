# Multi-stage Dockerfile for React Vite Frontend
# Stage 1: Build static bundle
FROM node:20-alpine AS build

WORKDIR /app

# Copy package descriptors
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source files
COPY . .

# Build production bundle
RUN npm run build

# Stage 2: Serve using Nginx
FROM nginx:alpine

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy static assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
