# Health AI Agent

A personal health assistant powered by PinAI SDK that analyzes health data, provides insights, and offers recommendations to help users make informed health decisions.

## Features

- **Blood Test Analysis**: Analyzes blood test results to identify abnormal values and provides insights
- **Vital Signs Monitoring**: Tracks and interprets vital signs like blood pressure, heart rate, etc.
- **Health Recommendations**: Provides personalized health recommendations based on user's health data
- **Interactive Chat Interface**: User-friendly chat interface to interact with the Health AI Agent

## Project Structure

```
healthai/
├── backend/           # FastAPI backend
│   ├── app/           # Application code
│   │   ├── agent/     # Health AI Agent implementation
│   │   ├── api/       # API endpoints
│   │   ├── models/    # Data models
│   │   └── utils/     # Utility functions
│   └── requirements.txt  # Python dependencies
├── frontend/          # Next.js frontend
│   └── health-ai-frontend/  # Next.js application
└── data/              # Sample health data
    └── sample_health_data.json  # Sample health data for testing
```

## Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn

## Setup

### Backend

1. Navigate to the backend directory:
   ```
   cd healthai/backend
   ```

2. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   - Copy the `.env` file and update the `PINAI_API_KEY` with your API key from [PinAI Agent platform](https://agent.pinai.tech/profile)

5. Start the backend server:
   ```
   uvicorn app.main:app --reload
   ```

   The backend will be running at http://localhost:8000

### Frontend

1. Navigate to the frontend directory:
   ```
   cd healthai/frontend/health-ai-frontend
   ```

2. Install dependencies:
   ```
   npm install
   # or
   yarn install
   ```

3. Start the development server:
   ```
   npm run dev
   # or
   yarn dev
   ```

   The frontend will be running at http://localhost:3000

## Usage

1. Open your browser and navigate to http://localhost:3000
2. Use the chat interface to interact with the Health AI Agent
3. Ask questions about your health data, such as:
   - "What were the results of my blood test?"
   - "How are my vital signs?"
   - "What health recommendations do you have for me?"

## API Documentation

The backend API documentation is available at http://localhost:8000/docs when the backend server is running.

## Built With

- [PinAI Agent SDK](https://github.com/PIN-AI/pinai_agent_sdk) - SDK for creating intelligent agents
- [FastAPI](https://fastapi.tiangolo.com/) - Modern, fast API framework for Python
- [Next.js](https://nextjs.org/) - React framework for building the frontend
- [Tailwind CSS](https://tailwindcss.com/) - CSS framework for styling

## License

This project is open source and available under the [MIT License](LICENSE).

## Acknowledgements

- [PinAI](https://agent.pinai.tech/) for providing the agent platform and SDK
- Sample health data is fictional and created for demonstration purposes only 