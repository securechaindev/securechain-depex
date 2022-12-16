# Depex Proyect

[![Docker Image Version (latest by date)](https://img.shields.io/docker/v/germanmt/depex?color=blue)](https://hub.docker.com/repository/docker/germanmt/depex)

## Deployment with docker

1. It is necessary to run command 'export DOCKER_BUILDKIT=1' in Ubuntu before start working with docker. If you are using Windows run command 'set DOCKER_BUILDKIT=1'

2. Create a .env file from template.env

3. Deploy
- First time --> Run command 'docker compose -f docker-compose-init.yml up --build' (Init dockerfile will seed MongoDB database with vulnerabilities and modeled package managers)
- After first Time --> Run command 'docker compose up --build'

4. Enter [here](http://0.0.0.0:8000/docs)

(It is recommended to use a GUI such as [MongoDB Compass](https://www.mongodb.com/en/products/compass) to see what information is being indexed)

## Extra information

1. Here they are the [GitHub releases](https://github.com/GermanMT/depex/releases)

2. Here they are the [DockerHub releases](https://hub.docker.com/r/germanmt/depex/tags)

3. How to get a GitHub [API key](https://github.com/settings/tokens)

4. How to get a NVD [API key](https://nvd.nist.gov/developers/request-an-api-key)
