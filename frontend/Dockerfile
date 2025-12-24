FROM node:20-alpine

WORKDIR /app

# Install dependencies first for better caching
COPY package*.json ./
RUN npm ci --only=production=false

# Copy application code
COPY . .

# Build the Next.js application
RUN npm run build

# Set environment
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

EXPOSE 3000

# Start the application
CMD ["npm", "start"]
