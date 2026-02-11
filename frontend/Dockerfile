FROM node:20-alpine

WORKDIR /app
RUN corepack enable

# Copy package files
COPY package.json pnpm-lock.yaml ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy application code
COPY . .

# Build application
RUN pnpm run build

# Expose port
EXPOSE 3000

# Run application
CMD ["pnpm", "start"]
