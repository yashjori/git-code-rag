# Production frontend image: build the static SPA, then serve it with
# nginx (which also reverse-proxies to the backend - see nginx.conf).
#
# nginx.conf is bind-mounted at runtime (docker-compose), not baked in
# here - it needs to be swappable without a rebuild during the one-time
# Let's Encrypt cert bootstrap (HTTP-only config first, then the real
# HTTPS config once a certificate exists).
FROM oven/bun:1 AS build

WORKDIR /app

COPY package.json bun.lock ./
RUN bun install --frozen-lockfile

COPY . .

# Same-origin deploy behind nginx: relative API paths, no CORS needed.
ARG VITE_API_BASE_URL=""
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
# HTTP-only deployments should not offer to send a PAT in plaintext.
ARG VITE_ENABLE_PRIVATE_TOKENS=true
ENV VITE_ENABLE_PRIVATE_TOKENS=$VITE_ENABLE_PRIVATE_TOKENS

RUN bun run build

FROM nginx:1.27-alpine

COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80 443
