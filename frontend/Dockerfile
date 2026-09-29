# Builds the Vue app, then serves it with Caddy, which also proxies /api to the backend.
# Same origin for the page and the API keeps the httpOnly auth cookie working.
FROM node:24-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM caddy:2-alpine
COPY Caddyfile /etc/caddy/Caddyfile
COPY --from=build /app/dist /srv
