# Build stage
FROM node:20-alpine as build

WORKDIR /app

# Install dependencies using clean install
COPY package*.json ./
RUN npm ci

# Copy source code and build
COPY . .
RUN npm run build

# Production serve stage using Nginx
FROM nginx:alpine

# Copy built assets from builder stage
COPY --from=build /app/dist /usr/share/nginx/html

# Replace default Nginx configuration with our custom SPA & Proxy config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port (default 80)
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
