# Base image
FROM node:14-alpine

# Set working directory
WORKDIR /app

# Copy and install dependencies
COPY ./aurora/package*.json ./
RUN npm install

# Copy project files
COPY . .

# Build the app
RUN npm run build

# Expose port 3000 for the app
EXPOSE 3000

# Start the app
CMD ["npm", "start"]
