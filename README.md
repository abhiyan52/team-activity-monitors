# Team Activity Monitor

A comprehensive full-stack application that monitors team activity across JIRA and GitHub, providing AI-powered insights through a natural language chat interface.

## Overview

Team Activity Monitor helps development teams track productivity and stay informed about project progress by integrating with:
- **JIRA** - Issue tracking, sprint planning, and project management
- **GitHub** - Code commits, pull requests, and repository activity
- **OpenAI** (optional) - AI-powered natural language responses and insights

## Features

- 🤖 **Natural Language Queries** - Ask questions in plain English about team activity
- 📊 **JIRA Integration** - Track issues, sprints, and project progress
- 🔄 **GitHub Integration** - Monitor commits, pull requests, and repository activity
- 🧠 **AI-Powered Insights** - Get intelligent summaries and recommendations
- 📱 **Responsive Web Interface** - Works on desktop and mobile devices
- 🔧 **Easy Configuration** - Simple setup with environment variables
- 📈 **Real-time Status** - Live monitoring of system health and connectivity

## Architecture

```
team-activity-monitor/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes (JIRA, GitHub, Activity)
│   │   ├── clients/        # External API clients
│   │   ├── core/           # Configuration and response templates
│   │   ├── models/         # Pydantic schemas
│   │   ├── utils/          # Utility functions
│   │   └── main.py         # FastAPI application
│   └── requirements.txt
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── api/           # API client
│   │   └── styles/        # CSS styling
│   └── package.json
└── README.md
```

## Quick Start

### Prerequisites

- **Python 3.8+** for the backend
- **Node.js 16+** and npm/yarn for the frontend
- **JIRA Account** (optional) with API access
- **GitHub Account** (optional) with personal access token
- **OpenAI API Key** (optional) for enhanced AI responses

### 1. Clone and Setup Environment

```bash
# Clone the repository (if from version control)
git clone <repository-url>
cd team-activity-monitor

# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the backend server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Documentation**: http://localhost:8000/docs

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm start
```

The frontend will be available at: http://localhost:3000

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

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

# OpenAI Configuration (optional)
OPENAI_API_KEY=your-openai-api-key

# Application Settings
DEBUG=false
LOG_LEVEL=INFO
```

### Getting API Keys

#### JIRA API Token
1. Go to [Atlassian API Tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click "Create API token"
3. Copy the generated token

#### GitHub Personal Access Token
1. Go to GitHub Settings > Developer settings > [Personal access tokens](https://github.com/settings/tokens)
2. Generate a new token with `repo` and `user` permissions
3. Copy the generated token

#### OpenAI API Key
1. Go to [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Create a new API key
3. Copy the key

## Usage Examples

Once both backend and frontend are running, try these natural language queries:

### Basic Queries
- "What has the team been working on this week?"
- "Show me recent GitHub activity"
- "What JIRA issues are in progress?"
- "Recent commits by team members"

### Team-Specific Queries
- "What has @john been working on?"
- "Show me commits by sarah in the last 5 days"
- "Recent pull requests by team members"

### Project/Repository Specific
- "GitHub activity in the frontend repo"
- "Issues in project ABC"
- "Show me pull requests from last week"
- "Commits in the backend repository"

### Time-Based Queries
- "Activity from yesterday"
- "What happened this month?"
- "Show me work from the last 30 days"

## API Endpoints

### Main Activity Endpoints
- `POST /api/activity/query` - Natural language team activity queries
- `GET /api/activity/status` - System health and integration status
- `GET /api/activity/recent-summary` - Recent activity summary

### JIRA Endpoints
- `GET /api/jira/health` - JIRA connection status
- `GET /api/jira/issues` - Get JIRA issues with filters
- `GET /api/jira/recent-activity` - Recent JIRA activity

### GitHub Endpoints
- `GET /api/github/health` - GitHub connection status
- `GET /api/github/repositories` - List available repositories
- `GET /api/github/commits` - Get commits with filters
- `GET /api/github/pull-requests` - Get pull requests
- `GET /api/github/recent-activity` - Recent GitHub activity

## Troubleshooting

### Common Issues

1. **Backend not starting**
   - Check Python version (3.8+ required)
   - Ensure all dependencies are installed
   - Verify environment variables are set correctly

2. **Frontend connection errors**
   - Ensure backend is running on port 8000
   - Check for CORS issues in browser console
   - Verify REACT_APP_API_URL if using custom backend URL

3. **JIRA integration not working**
   - Verify JIRA server URL is correct
   - Check API token permissions
   - Ensure username matches the token owner

4. **GitHub integration not working**
   - Verify GitHub token has correct permissions
   - Check if organization name is correct (if using)
   - Ensure token hasn't expired

5. **No AI responses**
   - OpenAI integration is optional
   - Check OpenAI API key is valid
   - Verify you have credits in your OpenAI account

### System Status

The application includes a built-in system status monitor that shows:
- Overall system health
- JIRA connection status
- GitHub connection status
- Configuration validation
- Helpful setup guidance

## Development

### Backend Development

```bash
cd backend
# Install development dependencies
pip install -r requirements.txt

# Run with auto-reload
uvicorn app.main:app --reload

# Run tests (if available)
pytest
```

### Frontend Development

```bash
cd frontend
# Start development server with hot reload
npm start

# Build for production
npm run build

# Run tests
npm test
```

### Code Structure

- **Backend**: FastAPI with clean architecture separating API routes, business logic, and external integrations
- **Frontend**: React with functional components, hooks, and modern CSS
- **API Client**: Centralized API communication with error handling
- **Styling**: Custom CSS with responsive design and modern aesthetics

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues, questions, or contributions:
1. Check the troubleshooting section
2. Review the system status in the application
3. Create an issue in the repository
4. Consult the individual README files in `backend/` and `frontend/` directories
