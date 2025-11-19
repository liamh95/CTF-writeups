FROM node:24-alpine

# Set the working directory inside the container
WORKDIR /app

# Copy package.json and package-lock.json to the working directory
# COPY package*.json ./

# Install application dependencies
RUN npm install

# Copy the rest of your application code
COPY . .

# Expose the port your Node.js application listens on
EXPOSE 3000

# Define the command to run your application
CMD [ "npm", "start" ]