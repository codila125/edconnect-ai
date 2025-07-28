# Masterminds Hackathon Project

A web application that uses AI to summarize educational materials, making them easier for students to understand. Teachers can create classes and upload PDF documents, and the application automatically generates and displays a concise summary.

## Features

-   **User Authentication:** Secure sign-in for teachers and students using Google OAuth.
-   **Classroom Management:** Teachers can create, manage, and share virtual classrooms.
-   **AI-Powered Summarization:** Upload PDF documents via URL, and the backend generates a detailed summary using a local AI model (Ollama).
-   **Content Delivery:** Students can join classes to view uploaded materials and their AI-generated summaries.

## Tech Stack

-   **Frontend:** React, Vite, TypeScript, TanStack Router, Tailwind CSS
-   **Backend:** Python, FastAPI
-   **Database:** NeonDB (PostgreSQL), Drizzle ORM
-   **Authentication:** Supabase, `better-auth`
-   **AI/ML:** Ollama (`qwen2.5vl:7b` model), EasyOCR
-   **Runtime:** Bun (Frontend), Python 3 (Backend)

## How it Works

1.  **Authentication:** A user signs in, and their role (teacher/student) is determined.
2.  **Content Creation (Teacher):** A teacher creates a class and adds new content by submitting a PDF link.
3.  **Backend Processing:** The URL is sent to the FastAPI backend.
4.  **AI Summarization:** The backend downloads the PDF, extracts its content (using OCR for images), and uses a local Ollama model to generate a summary.
5.  **Database Storage:** The summary is stored in the NeonDB database.
6.  **Content Viewing (Student):** Students join the class and can view the learning materials along with the helpful AI-generated summaries.

## Prerequisites

Before you begin, ensure you have the following installed:

-   [Bun](https://bun.sh/)
-   [Python](https://www.python.org/downloads/) (3.10 or newer)
-   [Ollama](https://ollama.com/): You must also pull the required model:
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
    d. Create a `.env` file in the `model` directory and add your database connection string:
    ```env
    # model/.env
    DATABASE_URL="your_neon_db_connection_string"
    ```
    e. Return to the root directory: `cd ..`

3.  **Frontend Setup:**
    a. Install dependencies: `bun install`
    b. Create a `.env` file in the root directory and add your project-specific keys. You can use the same `DATABASE_URL` from the backend setup.
    ```env
    # .env (root directory)
    VITE_SUPABASE_URL="your_supabase_project_url"
    VITE_SUPABASE_ANON_KEY="your_supabase_anon_key"
    DATABASE_URL="your_neon_db_connection_string"
    BETTER_AUTH_SECRET="a_long_random_secret_string"
    BETTER_AUTH_URL="http://localhost:5173/api/auth"
    GOOGLE_CLIENT_ID="your_google_oauth_client_id"
    GOOGLE_CLIENT_SECRET="your_google_oauth_client_secret"
    ```
    c. **Database Migrations:** This project uses Drizzle ORM. To push schema changes to your database, run:
    ```bash
    bunx drizzle-kit push
    ```

## Running the Application

You must start both the backend and frontend servers.

1.  **Start the Backend Server:**
    - Make sure Ollama is running.
    - In the `model` directory (with the virtual environment active):
    ```bash
    python main.py --serve
    ```
    The backend will run at `http://localhost:8000`.

2.  **Start the Frontend Server:**
    - In the root directory:
    ```bash
    bun run dev
    ```
    The frontend will run at `http://localhost:5173`.