# Installing Open Notebook


## 📦 Installing from Source

Quickly get started by cloning and installing the dependencies.

```sh
git clone https://github.com/lfnovo/open_notebook.git
cd open_notebook
poetry install
```

Make a copy of `example.env` and rename it to `.env`.

You need to enter at least your OPENAI_API_KEY and the Surreal DB connection details. 

```
OPENAI_API_KEY=

# CONNECTION DETAILS FOR YOUR SURREAL DB
SURREAL_ADDRESS="ws://localhost:8000/rpc"
SURREAL_USER="root"
SURREAL_PASS="root"
SURREAL_NAMESPACE="open_notebook"
SURREAL_DATABASE="staging"
```

Then, run it by using:

```sh
poetry run streamlit run app_home.py
```

or the shourcut

```sh
make run
```

## 🐳 Docker Setup

Alternatively, you can use Docker for easy setup.
Copy the `.env.example` file and name it `docker.env`

```sh
docker run -d \
  --name open_notebook \
  -p 8080:8502 \
  -v $(pwd)/docker.env:/app/.env \
  lfnovo/open_notebook:latest
```

You can pass the environment variables manually if you want:

```sh
docker run -d \
  --name open_notebook \
  -p 8080:8502 \
  -e OPENAI_API_KEY=API_KEY \
  -e DEFAULT_MODEL="gpt-4o-mini" \
  -e SURREAL_ADDRESS="ws://localhost:8000/rpc" \
  -e SURREAL_USER="root" \
  -e SURREAL_PASS="root" \
  -e SURREAL_NAMESPACE="open_notebook" \
  -e SURREAL_DATABASE="staging" \
  lfnovo/open_notebook:latest
```

If you need to run Surreal DB on docker as well, it's easier to just use docker-compose, like this:

```yaml
services:
  surrealdb:
    image: surrealdb/surrealdb:v2
    ports:
      - "8000:8000"
    volumes:
      - ./surreal-data:/mydata
    user: "${UID}:${GID}"
    command: start --log trace --user root --pass root rocksdb:mydatabase.db
    pull_policy: always
  open_notebook:
    image: lfnovo/open_notebook:latest
    ports:
      - "8080:8502"
    volumes:
      - ./docker.env:/app/.env
    depends_on:
      - surrealdb
    pull_policy: always
```

or with the environment variables:

```yaml
services:
  surrealdb:
    image: surrealdb/surrealdb:v2
    ports:
      - "8000:8000"
    volumes:
      - ./surreal-data:/mydata
    user: "${UID}:${GID}"
    command: start --log trace --user root --pass root rocksdb:mydatabase.db
    pull_policy: always
    open_notebook:
    image: lfnovo/open_notebook:latest
    ports:
        - "8080:8502"
    environment:
        - OPENAI_API_KEY=API_KEY
        - DEFAULT_MODEL=gpt-4o-mini
        - SURREAL_ADDRESS=ws://surrealdb:8000/rpc
        - SURREAL_USER=root
        - SURREAL_PASS=root
        - SURREAL_NAMESPACE=open_notebook
        - SURREAL_DATABASE=staging
    depends_on:
        - surrealdb
    pull_policy: always
```

## Running the app

After the app is running, you can access it at http://localhost:8080.

The first time you connect, it will check for the database and see if the schema is ready. If not, it will create the database for you. 