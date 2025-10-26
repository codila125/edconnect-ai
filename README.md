# ED-Connect AI

A web application that uses AI to summarize educational materials, making them easier for students to understand. Teachers can create classes and upload PDF documents, and the application automatically generates and displays a concise summary. Students can directly interact with teachers in real time for any queries.

## Features

- **User Authentication:** Secure sign-in for teachers and students using Google OAuth.
- **Classroom Management:** Teachers can create, manage, and share virtual classrooms.
- **AI-Powered Summarization:** Upload PDF documents via URL, and the backend generates a detailed summary using a local AI model (Ollama).
- **Content Delivery:** Students can join classes to view uploaded materials and their AI-generated summaries.
- **Realtime Communication** Students can directly communicate with their respective teachers.

## Tech Stack

- **Frontend:** React, Vite, TypeScript, TanStack Router, Tailwind CSS
- **Backend:** Python, FastAPI
- **Database:** NeonDB (PostgreSQL), Drizzle ORM
- **Authentication:** Supabase, `better-auth`
- **AI/ML:** Ollama (`qwen2.5vl:7b` model), EasyOCR
- **Runtime:** Bun (Frontend), Python 3 (Backend)

## How it Works

1.  **Authentication:** A user signs in, and their role (teacher/student) is determined.
2.  **Content Creation (Teacher):** A teacher creates a class and adds new content by submitting a PDF link.
3.  **Backend Processing:** The URL is sent to the FastAPI backend.
4.  **AI Summarization:** The backend downloads the PDF, extracts its content (using OCR for images), and uses a local Ollama model to generate a summary.
5.  **Database Storage:** The summary is stored in the NeonDB database.
6.  **Content Viewing (Student):** Students join the class and can view the learning materials along with the helpful AI-generated summaries. They can also interact after joining the class.

## Prerequisites

Before you begin, ensure you have the following installed:

- [Bun](https://bun.sh/)
- [Python](https://www.python.org/downloads/) (3.10 or newer)
- [Ollama](https://ollama.com/): You must also pull the required model:
    ```bash
    ollama pull qwen2.5vl:7b
    ```

## Setup and Installation

1.  **Clone the repository:**

    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Backend Setup:**
    a. Navigate to the `model` directory: `cd model`
    b. Create and activate a virtual environment:

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

    c. Install dependencies: `pip install -r requirements.txt`
    d. Change to root directory`cd ..`

3.  **Frontend Setup:**
    a. Install dependencies: `bun install`
    b. Create a `.env` file in the root directory and add your project-specific keys.
    ```env
    # .env (root directory)
    VITE_SUPABASE_URL="your_supabase_project_url"
    VITE_SUPABASE_ANON_KEY="your_supabase_anon_key"
    DATABASE_URL="your_neon_db_connection_string"
    BETTER_AUTH_SECRET="a_long_random_secret_string"
    BETTER_AUTH_URL="http://localhost:5173/api/auth"
    GOOGLE_CLIENT_ID="your_google_oauth_client_id"
    GOOGLE_CLIENT_SECRET="your_google_oauth_client_secret"
    MODEL="your_model_name"
    ```
    c. **Database Migrations:** This project uses Drizzle ORM. To push schema changes to your database, run:
    ```bash
    bunx drizzle-kit push
    ```

## Running the Application

You must start both the frontend, backend and ollama servers.

1.  **Start the Ollama Server:**
    If it's already not running,
    ```
    ollama serve
    ```
    The ollama will run at `http://localhost:11434`.

2.  **Start the FASTAPI Backend Server:**
    - Make sure Ollama is running.
    - In the `model` directory (with the virtual environment active):

    ```bash
    python main.py --serve
    ```

    The fast api backend will run at `http://localhost:8000`.

    ```
    "GET /": "This endpoint",
    "GET /summarize?pdf_url=<url>&model=<model>": "Summarize a PDF and update database",
    "GET /contents": "Get all contents with material URLs",
    "GET /contents/{id}": "Get content by ID",
    "GET /contents/by-url/{pdf_url}": "Get contents by PDF URL"
    ```

3.  **Start the React App:**
    - In the root directory:

    ```bash
    bun run dev
    ```

    The react app will run at `http://localhost:3000`.
