# GitHub Activity Tracker

## Overview
This application tracks activity on GitHub by monitoring up to **five configurable repositories**. It fetches events from the **GitHub Events API** and calculates the **average time between consecutive events** for each combination of event type and repository. The statistics are made available via a **FastAPI-based REST API**.

## Features
- Monitors up to **5 GitHub repositories**
- Maintains a rolling window of **7 days or 500 events (whichever is less)**
- Calculates the **average time between consecutive events)**
- Stores data persistently using **SQLite**
- Minimizes API calls to GitHub by caching and throttling requests
- Provides an API endpoint to retrieve statistics on event timing

## Installation
### Prerequisites
- Python 3.8+
- pip
- Git
- Docker (optional, for containerized deployment)

### Setup
1. Clone the repository:
   ```sh
   git clone https://github.com/your-username/github-tracker.git
   cd github-tracker
   ```

2. Create a virtual environment and install dependencies:
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```

3. Run the application:
   ```sh
   uvicorn main:app --reload
   ```

## API Endpoints
### Get Event Statistics
**Endpoint:** `GET /stats`

**Response Example:**
```json
{
  "stats": [
    {
      "repo_name": "owner/repo2",
      "event_type": "PushEvent",
      "average_time_between_events": 2800.5
    }
  ]
}
```

## Configuration
You can configure the repositories to track by modifying the `REPOSITORIES` list in `main.py`:
```python
REPOSITORIES = ["owner/repo1", "owner/repo2", "owner/repo3", "owner/repo4", "owner/repo5"]
```

## Deployment
### Using Docker
1. Build the Docker image:
   ```sh
   docker build -t github-tracker .
   ```

2. Run the container:
   ```sh
   docker run -p 8000:8000 github-tracker
   ```

## Assumptions
- The application is configured to fetch data every **10 seconds per repository** to avoid hitting rate limits.
- A rolling window of **7 days or 500 events** ensures we only store recent data.
- SQLite is used for persistence, but can be replaced with PostgreSQL or another database for production.

## License
MIT License

