# Chewy Customer Sentiment Analysis Agent

## Overview
A full-stack AI agent that analyzes customer sentiment for products based on SKU input. It queries Snowflake for customer reviews, processes them through a LangGraph pipeline, and displays results in a modern React UI.

## Tech Stack
- **Frontend**: Next.js (React, TypeScript, Tailwind CSS)
- **Backend**: Python FastAPI, LangGraph, scikit-learn, KeyBERT, OpenAI
- **Database**: Snowflake
- **AI Models**: OpenAI GPT-4.1, text-embedding-3-small, gpt-4.1-nano

## Project Structure
```
chewy-customer-sentiment-analysis-agent/
├── frontend/                    # Next.js React app
│   ├── components/
│   ├── hooks/
│   ├── pages/
│   ├── styles/
│   ├── utils/
│   └── types/
├── backend/                     # Python FastAPI server
│   ├── models/
│   ├── nodes/
│   ├── core/
│   ├── api/
│   ├── utils/
│   └── main.py
├── .env.template
├── requirements.txt
├── package.json
└── README.md
```

## Setup
### Prerequisites
- Node.js 18+
- Python 3.8+
- Snowflake account & credentials
- OpenAI API key

### Installation
```bash
npm install
pip install -r requirements.txt
```

### Running the App
```bash
npm run dev  # Starts both frontend and backend
```

## Usage
1. Enter a SKU in the input field.
2. Track progress in real-time.
3. View executive summary, stats, and sample reviews.
4. Export results as PDF/JSON.

## Environment Variables
See `.env.template` for required variables.

## Testing
- Frontend: Jest, React Testing Library
- Backend: pytest

## License
MIT 