# Depex

## What is Depex?

Depex is a tool that allows you to reason over the entire configuration space of the Software Supply Chain of an open-source software repository.

## Development

### Development requirements

1. [Docker](https://www.docker.com/) to deploy the tool.
2. [Docker Compose](https://docs.docker.com/compose/) for container orchestration.

### Deployment with docker

#### Step 1
Create a `.env` file from the `template.env` file and place it in the `app/` directory.

##### Get API Keys

- How to get a *GitHub* [API key](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens).

- Modify the **Json Web Token (JWT)** secret key and algorithm with your own. You can generate your own secret key with the command **openssl rand -base64 32**.

#### Step 2
Ensure you have the `securechain` Docker network created. If not, create it with:
```bash
docker network create securechain
```

#### Step 3
Run the command from the project root:
```bash
docker compose -f dev/docker-compose.yml up --build
```

#### Step 4
The API will be available at [http://localhost:8002](http://localhost:8002). You can access the API documentation at [http://localhost:8002/docs](http://localhost:8002/docs).

### Other tools
1. It is recommended to use a GUI such as [MongoDB Compass](https://www.mongodb.com/en/products/compass) to see what information is being indexed in vulnerability database.

2. You can see the graph built [here](http://0.0.0.0:7474/browser/), using the Neo4J browser interface.

### Python Environment
The project uses Python 3.13 and the dependencies are listed in `requirements.txt`.

#### Setting up the development environment

1. **Create a virtual environment**:
   ```bash
   python3.13 -m venv depex-env
   ```

2. **Activate the virtual environment**:
   ```bash
   # On Linux/macOS:
   source depex-env/bin/activate
   
   # On Windows:
   depex-env\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Project Structure
- `app/` - Main application code
  - `apis/` - External API services (GitHub, package managers)
  - `controllers/` - API endpoint controllers
  - `schemas/` - Data validation schemas
  - `services/` - Business logic services
  - `utils/` - Utility functions and graph builders
- `dev/` - Development configuration (Docker files)
