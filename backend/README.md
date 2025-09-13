# Team Activity Monitor Backend

FastAPI backend for the Team Activity Monitor application that integrates with JIRA and GitHub to provide team activity insights.

## Features

- **JIRA Integration**: Fetch and analyze JIRA issues, track team member activity
- **GitHub Integration**: Monitor commits, pull requests, and repository activity
- **Natural Language Queries**: Parse natural language queries to extract team members, date ranges, and filters
- **AI-Powered Responses**: Generate intelligent summaries using OpenAI (optional)
- **RESTful API**: Well-documented API endpoints for frontend integration

## Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the backend directory:

```bash
# Database
DATABASE_URL=sqlite:///./team_activity.db

# JIRA Configuration (optional)
JIRA_SERVER_URL=https://your-company.atlassian.net
JIRA_USERNAME=your-email@company.com
JIRA_API_TOKEN=your-jira-api-token

# GitHub Configuration (optional)
GITHUB_TOKEN=your-github-personal-access-token
GITHUB_ORGANIZATION=your-org-name

# OpenAI Configuration (optional - for enhanced AI responses)
OPENAI_API_KEY=your-openai-api-key

# Application Settings
DEBUG=false
LOG_LEVEL=INFO
```

### 3. Getting API Tokens

#### JIRA API Token:
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Copy the generated token

#### GitHub Personal Access Token:
1. Go to GitHub Settings > Developer settings > Personal access tokens
2. Generate a new token with appropriate permissions (repo, user)
3. Copy the generated token

#### OpenAI API Key (optional):
1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Copy the key

## Running the Application

### Development Mode

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Production Mode

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Interactive API docs: http://localhost:8000/docs
- ReDoc documentation: http://localhost:8000/redoc

## API Endpoints

### Main Activity Endpoints

- `POST /api/activity/query` - Query team activity with natural language
- `GET /api/activity/status` - Get system status
- `GET /api/activity/recent-summary` - Get recent activity summary
- `POST /api/activity/parse-query` - Parse natural language query

### JIRA Endpoints

- `GET /api/jira/health` - Check JIRA connection
- `GET /api/jira/issues` - Get JIRA issues with filters
- `GET /api/jira/recent-activity` - Get recent JIRA activity

### GitHub Endpoints

- `GET /api/github/health` - Check GitHub connection
- `GET /api/github/repositories` - List repositories
- `GET /api/github/commits` - Get commits with filters
- `GET /api/github/pull-requests` - Get pull requests
- `GET /api/github/recent-activity` - Get recent GitHub activity

## Example Queries

The system supports natural language queries like:

```
"What has @john been working on this week?"
"Show me all commits by sarah in the last 5 days"
"What issues are in progress for project ABC?"
"GitHub activity for the team this month"
"Recent pull requests in the frontend repo"
```

## Architecture

```
app/
├── api/                 # API route handlers
├── clients/            # External API clients (JIRA, GitHub)
├── core/               # Core application logic and config
├── models/             # Pydantic schemas
├── utils/              # Utility functions
└── main.py            # FastAPI application entry point
```

## Error Handling

The API includes comprehensive error handling:
- Invalid configuration returns appropriate error messages
- API connection failures are gracefully handled
- Invalid queries return helpful error responses
- All endpoints include proper HTTP status codes

## Logging

Application logs include:
- API request/response information
- External API call status
- Error details and stack traces
- Performance metrics

## Testing

```bash
# Run with test database
DATABASE_URL=sqlite:///./test.db uvicorn app.main:app --reload

# Test specific endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/activity/status
```
