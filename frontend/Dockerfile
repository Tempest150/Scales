# Scales web UI (Vite + React) — dev image. Runs the Vite dev server with HMR.
FROM node:22-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

ENV VITE_HOST=0.0.0.0
EXPOSE 5173

CMD ["npm", "run", "dev"]
