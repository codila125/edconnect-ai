# Masterminds Hackathon

This project is a full-stack web application developed for the Masterminds Hackathon. It features a React-based frontend and a Python-based backend with OCR capabilities.

## Tech Stack

### Frontend

- **Framework:** React
- **Build Tool:** Vite
- **Routing:** TanStack Router
- **Styling:** Tailwind CSS
- **Database ORM:** Drizzle ORM
- **Backend Service:** Supabase

### Backend

- **Framework:** FastAPI
- **Database:** SQLAlchemy
- **PDF Processing:** PyMuPDF, PyPDF2
- **OCR:** EasyOCR, OpenCV

## Getting Started

### Prerequisites

- Node.js and Bun
- Python 3.12+
- PostgreSQL

### Installation

1.  **Frontend:**
    ```bash
    bun install
    ```

2.  **Backend:**
    ```bash
    pip install -r model/requirements.txt
    ```

### Running the Application

1.  **Frontend:**
    ```bash
    bun run dev
    ```

2.  **Backend:**
    ```bash
    uvicorn model.main:app --reload
    ```

## Features

- User authentication
- Create and join classes
- Add and view class content
- Real-time chat
- OCR functionality to extract text from PDFs
- and many more...
