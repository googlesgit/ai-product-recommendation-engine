FROM node:20-alpine

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

ENV VITE_API_URL=http://localhost:5001/api

EXPOSE 3000
CMD ["npm", "start"]
