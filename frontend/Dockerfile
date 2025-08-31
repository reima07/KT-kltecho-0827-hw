# Build stage
FROM node:20-alpine AS build-stage
WORKDIR /app
COPY package*.json ./
# package-lock.json이 있으면 ci가 더 안전
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi
COPY . .
# webpack4 기반 프로젝트가 Node 17+에서 OpenSSL 이슈 나면 아래 줄을 임시로 열어주세요
# ENV NODE_OPTIONS=--openssl-legacy-provider
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=build-stage /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"] 