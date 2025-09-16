# Team Activity Monitor Backend

FastAPI backend for the Team Activity Monitor application that integrates with JIRA and GitHub to provide team activity insights through AI-powered natural language processing.

## Features

- **JIRA Integration**: Fetch and analyze JIRA issues, track team member activity
- **GitHub Integration**: Monitor commits, pull requests, and repository activity
- **AI-Powered Intent Parsing**: Advanced natural language understanding to extract user intent
- **Intelligent Agent System**: Context-aware agent that uses parsed intent to guide tool selection
- **Persistent Memory**: Conversation history maintained across sessions
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

# Google Gemini Configuration (for AI intent parsing and responses)
GOOGLE_API_KEY=your-google-gemini-api-key

# OpenAI Configuration (optional - for enhanced AI responses)
OPENAI_API_KEY=your-openai-api-key

# Application Settings
DEBUG=false
LOG_LEVEL=INFO

# Cache Configuration (optional - uses file-based cache by default)
CACHE_DIR=cache
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

#### Google Gemini API Key (required):
1. Go to https://makersuite.google.com/app/apikey
2. Create a new API key
3. Copy the key

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

- `POST /api/activity/query` - Query team activity with natural language (uses AI intent parsing)
- `GET /api/activity/status` - Get system status
- `GET /api/activity/recent-summary` - Get recent activity summary
- `POST /api/activity/parse-query` - Parse natural language query

### Conversation Endpoints

- `POST /api/conversations/` - Create new conversation thread
- `POST /api/conversations/{thread_id}/messages` - Send message to conversation
- `GET /api/conversations/{thread_id}/messages` - Get conversation history
- `GET /api/conversations/{thread_id}/memory` - Get agent memory summary

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

The system supports natural language queries with AI-powered intent understanding:

```
"What has @john been working on this week?"
"Show me all commits by sarah in the last 5 days"
"What issues are in progress for project ABC?"
"GitHub activity for the team this month"
"Recent pull requests in the frontend repo"
"Who worked on the authentication feature?"
"Show me John's activity across all projects"
```

## Conversation System

The system maintains persistent conversation memory across sessions:

### Features:
- **Thread-Based Memory**: Each conversation thread maintains its own context
- **Context Awareness**: Follow-up questions reference previous responses
- **Memory Persistence**: Conversation history stored in database
- **Agent State**: AI agent remembers previous interactions within a thread

### Usage:
```python
# Create conversation thread
POST /api/conversations/
{
  "title": "Team Activity Discussion"
}

# Send messages with context
POST /api/conversations/{thread_id}/messages
{
  "content": "What did John work on this week?"
}

# Follow-up with context
POST /api/conversations/{thread_id}/messages
{
  "content": "What about Sarah?"
}
```

## AI Architecture

The system uses a two-stage AI approach for intelligent query processing:

### 1. Intent Parser (`intent_parser.py`)
The **AgentIntentParser** is responsible for understanding user queries and converting them into structured execution plans.

**Key Features:**
- **Natural Language Understanding**: Analyzes user queries to extract intent, team members, projects, and time ranges
- **Context Awareness**: Uses conversation history to provide better intent parsing
- **JSON Output**: Generates structured JSON with recommended operations and filters
- **Tool Mapping**: Maps user intent to specific JIRA and GitHub tools

**Example Output:**
```json
{
  "is_relevant": true,
  "intent": "Find recent activities for John this week",
  "operations": [
    {
      "tool": "get_recent_activity",
      "action": "Get activity for John across JIRA and GitHub",
      "filters": {"team_members": ["john", "john.doe"], "days": 7}
    }
  ],
  "members": ["john", "john.doe"],
  "time_range": {"label": "this week"}
}
```

### 2. Basic Agent (`basic_agent.py`)
The **BasicAgent** executes the parsed intent using available tools and provides intelligent responses.

**Key Features:**
- **Intent-Driven Execution**: Uses parsed JSON to guide tool selection and filtering
- **Persistent Memory**: Maintains conversation context across sessions
- **Tool Integration**: Seamlessly integrates with JIRA and GitHub APIs
- **Fallback Handling**: Gracefully handles parsing failures with basic agent mode

**Workflow:**
1. **Parse Intent**: Extract structured information from user query
2. **Check Relevance**: Validate if query is related to JIRA/GitHub activities
3. **Execute Tools**: Use recommended tools with suggested filters
4. **Generate Response**: Combine tool outputs into coherent answer

## Architecture

```
app/
├── api/                 # API route handlers
├── clients/            # External API clients (JIRA, GitHub)
├── core/               # Core application logic and config
│   ├── services/       # AI services (intent_parser.py, basic_agent.py)
│   ├── tools.py        # Tool definitions for JIRA/GitHub
│   └── config.py       # Application configuration
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

## Technical Implementation

### AI Components

**Intent Parser (`intent_parser.py`):**
- Uses Google Gemini 1.5 Flash for natural language understanding
- Generates structured JSON with user intent, operations, and filters
- Includes comprehensive examples and context for accurate parsing
- Handles conversation history for context-aware responses

**Basic Agent (`basic_agent.py`):**
- Integrates LangChain agents with OpenAI Functions format
- Uses persistent memory for conversation continuity
- Implements fallback mechanisms for robust error handling
- Supports thread-based agent instances for multi-user scenarios

### Key Technologies

- **LangChain**: Agent framework and tool integration
- **Google Gemini**: AI model for intent parsing and responses
- **FastAPI**: RESTful API framework
- **SQLAlchemy**: Database ORM for conversation persistence
- **Pydantic**: Data validation and serialization

### Database Schema

The system uses SQLite/PostgreSQL with the following key tables:
- `conversation_threads`: Conversation metadata
- `conversation_messages`: Individual messages with timestamps
- `agent_sessions`: Agent memory state per thread

## Testing

```bash
# Run with test database
DATABASE_URL=sqlite:///./test.db uvicorn app.main:app --reload

# Test specific endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/activity/status

# Test AI functionality
curl -X POST http://localhost:8000/api/activity/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What did John work on this week?"}'
```
