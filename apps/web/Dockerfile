# React app built with Vite, served by nginx on 8080.
# Build context is the repo root (npm workspace); ignores are in Dockerfile.dockerignore.
#   docker buildx build -f apps/web/Dockerfile \
#     --build-arg VITE_COGNITO_USER_POOL_ID=... --build-arg VITE_COGNITO_APP_CLIENT_ID=... .

FROM node:22-alpine AS build
WORKDIR /app

# Install deps first so this layer is cached until a package.json changes
COPY package.json package-lock.json ./
COPY apps/web/package.json apps/web/
COPY packages/ui/package.json packages/ui/
RUN npm ci

COPY apps/web apps/web
COPY packages/ui packages/ui

# Vite inlines these at build time. Empty VITE_API_URL = same-origin /api.
ARG VITE_COGNITO_USER_POOL_ID
ARG VITE_COGNITO_APP_CLIENT_ID
ARG VITE_API_URL=""
ARG VITE_DEMO_IMAGES=""
ENV VITE_COGNITO_USER_POOL_ID=$VITE_COGNITO_USER_POOL_ID \
    VITE_COGNITO_APP_CLIENT_ID=$VITE_COGNITO_APP_CLIENT_ID \
    VITE_API_URL=$VITE_API_URL \
    VITE_DEMO_IMAGES=$VITE_DEMO_IMAGES
RUN npm run build -w apps/web

FROM nginx:1.27-alpine
COPY apps/web/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/apps/web/dist /usr/share/nginx/html
EXPOSE 8080
