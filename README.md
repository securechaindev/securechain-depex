# Depex Proyect

<p>
  <a href="https://hub.docker.com/repository/docker/germanmt/depex" target="_blank">
    <img src="https://img.shields.io/docker/v/germanmt/depex?color=blue&label=dockerhub&logo=docker&sort=semver" alt="dockerhub">
  </a>

  <a href="https://github.com/GermanMT/depex/releases" target="_blank">
    <img src="https://img.shields.io/github/v/release/GermanMT/depex?color=green&logo=github" alt="release">
  </a>

  <a href="https://github.com/GermanMT/depex/blob/main/LICENSE.md" target="_blank">
    <img src="https://img.shields.io/github/license/GermanMT/depex?logo=gnu" alt="license">
  </a>

  <a href="https://github.com/GermanMT/depex/actions/workflows/analisys.yml" target="_blank">
    <img src="https://img.shields.io/github/actions/workflow/status/GermanMT/depex/analisys.yml?branch=main&event=push&label=code%20analisys" alt="code analisys">
  </a>
  
  <a href="https://doi.org/10.5281/zenodo.7612766">
    <img src="https://zenodo.org/badge/DOI/10.5281/zenodo.7612766.svg" alt="DOI">
  </a>
</p>

## Deployment with docker

1. Create a .env file from template.env

2. Deploy
- First time --> Run command 'docker compose -f docker-compose-init.yml up --build' (Init dockerfile will seed MongoDB database with vulnerabilities and modeled package managers)
- After first Time --> Run command 'docker compose up --build'

3. Enter [here](http://0.0.0.0:8000/docs)

(It is recommended to use a GUI such as [MongoDB Compass](https://www.mongodb.com/en/products/compass) to see what information is being indexed)

## Extra information

1. How to get a GitHub [API key](https://github.com/settings/tokens)

2. How to get a NVD [API key](https://nvd.nist.gov/developers/request-an-api-key)
