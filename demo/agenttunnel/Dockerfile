FROM alpine
RUN apk update && apk add yarn

WORKDIR /app
COPY package.json ./
COPY yarn.lock ./
RUN yarn install
COPY index.js ./

ENTRYPOINT ["yarn", "node", "./index.js"]
