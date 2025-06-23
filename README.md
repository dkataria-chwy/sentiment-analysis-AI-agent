# Customer Sentiment Analysis AI Agent

## Project Overview
This project is a research and experimentation platform to explore the use of Large Language Models (LLMs) and GPT for customer sentiment analysis. It provides a full-stack AI-powered solution to ingest, clean, analyze, and summarize customer reviews, surfacing actionable insights for business leadership and analysts.

## Key Features
- **Automated Review Ingestion:** Fetches customer reviews for a given SKU from a data warehouse (e.g., Snowflake).
- **Advanced Text Cleaning:** Multi-step pipeline (HTML, encoding, emoji, control, whitespace) with both classic and LLM-based options.
- **Embedding & Classification:** Uses vector embeddings and a logistic regression model for sentiment classification.
- **Keyword Extraction:** Identifies key themes and topics from reviews.
- **Statistical Analysis:** Computes review stats and sentiment breakdowns.
- **Executive Summary:** Generates a GPT-powered summary of customer sentiment and key findings.
- **Modern UI:** Next.js frontend with real-time progress, stepper, and logs for transparency.

## Architecture
- **Backend:** Python (FastAPI)
  - Async job orchestration and step tracking
  - Classic and LLM-based text cleaning
  - Sentiment model inference
  - REST API for job control and status
- **Frontend:** Next.js (React, TypeScript)
  - Dashboard for job submission and monitoring
  - Stepper UI with real-time progress and logs
  - Executive summary and data visualizations

## Setup Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+
- (Optional) Access to Snowflake or your review data source

### 1. Clone the Repository
```sh
git clone https://github.com/dkataria-chwy/sentiment-analysis-AI-agent.git
cd sentiment-analysis-AI-agent
```

### 2. Backend Setup
```sh
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
# (Optional) Set up your Snowflake credentials in .env
cd backend
python main.py
```
- The backend runs on `http://localhost:8000`

### 3. Frontend Setup
```sh
cd frontend
npm install
npm run dev
```
- The frontend runs on `http://localhost:3000`

### 4. Usage
- Open the frontend in your browser.
- Enter a SKU and start the analysis.
- Monitor progress in the dashboard stepper and logs.
- View the executive summary and sentiment breakdowns when complete.

## Customization
- **Text Cleaning:** Switch between classic and LLM-based cleaning in backend config.
- **Model:** Replace or retrain the sentiment model in `backend/models/` as needed.
- **Data Source:** Adapt the review ingestion logic for your data warehouse or API.

## Contribution & Notes
- This project is for research and experimentation. For production, further security, error handling, and scaling would be needed.
- Please open issues or pull requests for improvements.

---

© 2025 Darshan Kataria & Contributors 