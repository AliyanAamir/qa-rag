# 🧠 RAG Task API (FastAPI + Docker)

This is a FastAPI-based Retrieval-Augmented Generation (RAG) backend project. It uses PostgreSQL with the `pgvector` extension for similarity search and document embeddings.

---

## 🚀 Features

- FastAPI backend
- PostgreSQL with pgvector support
- Environment variable configuration
- Dockerized for local development

---

## 📁 Project Structure

```
.
├── app/
│   ├── routes/
│   ├── service/
│   ├── utils/
│   └── main.py
├── data/
├── Dockerfile
├── .env
├── docker-compose.yml
```

---

## ⚙️ Requirements

- Docker
- Docker Compose

---

## 📦 Setup Instructions

1. **Clone the repository**

```bash
git clone https://github.com/AliyanAamir/qa-rag.git 
cd rag-task
```

2. **Create a `.env` file**

Make sure you have a `.env` file in the root directory with the following variables:

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=rag_db
DATABASE_URL=postgresql://postgres:password@rag-postgres:5432/rag_db
EMBEDDING_MODEL=name-of-embedding-model
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
OPENAI_API_KEY=your-open-ai-key
```

3. **Build and start the containers**

```bash
docker-compose up --build
```

4. **Access the FastAPI app**

Once the app is running, open your browser and go to:

```
http://localhost:8000
```

Swagger UI is available at:

```
http://localhost:8000/docs
```

---

## 🐳 Docker Services

- **web**: FastAPI app running with Uvicorn
- **postgres**: PostgreSQL with `pgvector` for embeddings

---

## 🧪 Testing the API

Use tools like [Postman](https://www.postman.com/) or [httpie](https://httpie.io/) to test your endpoints, or simply use the `/docs` Swagger UI.

---

## 🧹 Cleanup

To stop and remove containers, volumes, and networks:

```bash
docker-compose down -v
```

---
