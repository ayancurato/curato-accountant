# Curato AI Expense & Finance Backend

This is the lightweight backend for the Curato AI Expense & Finance application.

## Overview
This application processes invoices using Groq AI (`qwen/qwen3.8-27b`), extracts financial structures, validates them, manages a simple balance sheet, and provides expense reporting.

### Invoice Processing Architecture
1. **Upload**: PDF or Image files are uploaded.
2. **Extraction**: `PyMuPDF` converts PDFs to images. Groq Vision Model extracts structured JSON (vendor, invoice number, dates, net amount, detailed tax breakdown like GST/VAT, and totals).
3. **Validation**: Python enforces strict rules (e.g. `net + tax = total`), matching against predefined categories, and checks for duplicates.
4. **Expense Draft**: The system creates a `NEEDS_REVIEW` expense.
5. **Approval**: Users can edit or approve.
6. **Balance Sheet**: Approved expenses instantly update the simplified Balance Sheet.

### Accounting Logic
The Balance Sheet is kept lightweight but consistent: `Assets = Liabilities + Equity - Expenses`.
For an approved invoice:
- **Debit** `General Expenses` (Expense account) for the Net Amount.
- **Debit** `Input GST/VAT Recoverable` (Asset account) for the Tax Amount.
- **Credit** `Accounts Payable` (Liability account) for the Total Amount.
This ensures the balance equation is perfectly satisfied.

## Architecture
- **Framework**: FastAPI
- **Database**: PostgreSQL (via SQLAlchemy & Alembic)
- **AI Processing**: Groq Vision API
- **Containerization**: Docker Compose

## Requirements
- Python 3.12+
- PostgreSQL 15+ (or Docker)

## Setup & Run Locally
1. **Environment Variables**:
   Copy `.env.example` to `.env` and fill in the values.
   ```bash
   cp .env.example .env
   ```
   Add your `GROQ_API_KEY`. (Set to `mock-api-key` for offline testing without real AI calls).

2. **Database Setup**:
   Start PostgreSQL using Docker:
   ```bash
   docker-compose up -d postgres
   ```
   Or use a local PostgreSQL instance and update `DATABASE_URL` in `.env`.

3. **Install Dependencies**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Migrations**:
   ```bash
   alembic upgrade head
   ```

5. **Seed Default Data**:
   ```bash
   python scripts/seed.py
   ```
   This will create a default CEO user (`ceo@curato.com` / `password123`), Curato categories, and default Balance Sheet accounts.

6. **Run Application**:
   ```bash
   uvicorn app.main:app --reload
   ```
   API Documentation (Swagger UI): http://localhost:8000/docs

## Running Tests
Tests use an in-memory SQLite database and mock the Groq AI response by default.
```bash
pytest
```

To run the optional live Groq integration test, set a real `GROQ_API_KEY` in your environment variables before running pytest.
