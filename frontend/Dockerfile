# Stage 1: Build the React application with Vite
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
# The build command is the same, but the tool is different
RUN npm run build

# Stage 2: Serve the application using Nginx
FROM nginx:1.25-alpine
# The output folder is 'dist', not 'build'
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]