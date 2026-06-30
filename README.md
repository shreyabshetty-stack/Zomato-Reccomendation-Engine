# Zomato Restaurant Recommender

An AI-powered restaurant recommendation system that combines structured filtering on a Zomato dataset with Groq's LLM (`llama-3.3-70b-versatile`) to rank and explain recommended restaurants.

## Project Structure

```text
restaurant-recommender/
??? docs/                      # Documentation files (problem statement, architecture, plan)
??? src/                       # Main application sources
?   ??? data/                  # Data loading, preprocessing, and schemas
?   ??? input/                 # User preference parsing and validation
?   ??? integration/           # Filtering logic and LLM prompt generation
?   ??? engine/                # Groq API provider, response parser, and recommender orchestrator
?   ??? output/                # UI rendering
?   ??? config.py              # Application settings and environment configuration
?   ??? main.py                # Streamlit UI entry point
??? tests/                     # Unit and integration tests
??? requirements.txt           # Python package dependencies
??? .env.example               # Template environment configuration
??? .gitignore                 # Files excluded from git tracking
```

## Setup & Run

1. **Initialize the Virtual Environment**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Copy `.env.example` to `.env` and fill in your details:
   ```bash
   copy .env.example .env
   ```
   Add your `GROQ_API_KEY` obtained from [console.groq.com](https://console.groq.com/).

4. **Verify Configuration**:
   ```bash
   python -c "from src import config"
   ```
