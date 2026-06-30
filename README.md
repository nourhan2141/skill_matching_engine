---
title: Skill Matching Engine
emoji: 🎯
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
---
# AI Career Coach API

A powerful FastAPI-based backend application designed to match Resumes (CVs) against Job Descriptions. It leverages **Groq** and the **Llama 3.1 8B** model to provide intelligent, AI-driven career coaching and skill matching insights.

## Features

- **AI-Powered Matching:** Analyzes CVs and job descriptions using Llama 3.1 8B (via Groq API).
- **Secure:** Protects all endpoints using a custom `X-API-Key` header authentication.
- **Rate Limited:** Integrates `slowapi` to prevent abuse and manage traffic.
- **Interactive Documentation:** Automatic Swagger UI generation accessible directly from the browser.
- **Fast & Modern:** Built on top of FastAPI and Uvicorn.
- **Dependency Management:** Uses `uv` for blazing-fast virtual environment and package management.

---

## Prerequisites

- **Python 3.10+**
- **uv:** The ultra-fast Python package installer and resolver.
  *(If you don't have `uv` installed, you can install it via pip: `pip install uv`)*
- A **Groq API Key** (Get one from [Groq Console](https://console.groq.com/))

---

## Setup & Installation

1. **Clone the repository** (or navigate to your project directory):
   ```bash
   cd skill_matching_engine
   ```

2. **Create a virtual environment and install dependencies using `uv`**:
   ```bash
   uv venv
   uv pip install -r requirements.txt
   ```

3. **Activate the virtual environment**:
   - **Windows (PowerShell):**
     ```powershell
     .venv\Scripts\activate
     ```
   - **macOS / Linux:**
     ```bash
     source .venv/bin/activate
     ```

---

## Configuration

The application requires some environment variables to run. 

1. Create a `.env` file in the root directory of the project (you can copy `.env.example` if it exists).
2. Add your keys to the `.env` file:

```env
# Your Groq API Key used by the backend to communicate with the Groq AI service
GROQ_API_KEY="gsk_your_groq_api_key_here"

# A secure key that YOU define. Clients must send this key in the X-API-Key header to use your API.
APP_API_KEY="your_secure_api_key_here"
```

---

## Running the Application

You can start the server in development mode (with auto-reload) using Uvicorn:

```bash
uvicorn app.main:app --reload
```

Alternatively, you can run the provided `run.py` script:
```bash
python run.py
```

The API will start at `http://127.0.0.1:8000`.

---

## Usage & Authentication

Because the API endpoints are protected, you cannot access them directly in a standard web browser without passing the `X-API-Key` header.

### 1. Interactive Documentation (Swagger UI)
You can view the interactive API documentation and test endpoints directly from your browser:
- **URL:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) (or simply `http://127.0.0.1:8000/` which redirects here).
- **To Authenticate:** Click the **"Authorize"** button at the top right of the page and enter your `APP_API_KEY`.

### 2. cURL Example
To make a request from your terminal, include the `X-API-Key` header:

```bash
curl -H "X-API-Key: your_secure_api_key_here" http://127.0.0.1:8000/
```

*(Note for Windows users: you might need to use `curl.exe` instead of `curl` in PowerShell to bypass the built-in alias)*.

---

## Project Structure

```text
skill_matching_engine/
├── .env                 # Environment variables (not tracked in git)
├── .venv/               # Virtual environment directory
├── requirements.txt     # Python dependencies
├── run.py               # Alternative entry point for the application
├── app/
│   ├── main.py          # FastAPI application initialization & configuration
│   ├── api/             # API routing and authentication logic
│   ├── core/            # Core configuration, LLM setup, and rate limiting (slowapi)
│   ├── schemas/         # Pydantic models for data validation
│   └── services/        # Business logic for CV and Job Description matching
├── tests/               # Unit and integration tests
└── scripts/             # Utility and helper scripts
```
