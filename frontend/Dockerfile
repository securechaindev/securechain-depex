FROM node:20.4.0

WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json ./

RUN npm install

COPY frontend/ ./

EXPOSE 3000

CMD npm start