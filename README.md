# flask-shop
An flask shop that only exposes an rest api

Shop admin and API is provided by Flask.
You will need a frontend. This project is an api first webshop with a Clojure/ReactJS based frontend.

Todo: add instruction to make a production build of the frontend and add it to the docker

# Build docker container suitable for hosting
docker build -t flask-shop .
docker run -d --name flask-shop -p 80:80 flask-shop
