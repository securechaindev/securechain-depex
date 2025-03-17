FROM node:alpine3.21

WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json ./

RUN npm install

EXPOSE 3000

CMD npm start
