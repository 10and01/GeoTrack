FROM node:20-alpine

WORKDIR /app

# Install dependencies in a cache-friendly layer. The lockfile keeps the
# classroom demo reproducible across machines.
COPY package*.json ./
RUN npm ci

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
