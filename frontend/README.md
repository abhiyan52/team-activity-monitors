# Team Activity Monitor Frontend

React frontend for the Team Activity Monitor application - a modern web interface for tracking team productivity across JIRA and GitHub.

## Features

- **Chat Interface**: Natural language queries for team activity insights
- **Real-time System Status**: Monitor JIRA and GitHub integration health
- **Rich Data Display**: Interactive views of issues, commits, and pull requests
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Error Handling**: Graceful handling of API errors with helpful feedback

## Prerequisites

- Node.js 16+ and npm/yarn
- Team Activity Monitor backend running on `http://localhost:8000`

## Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

Or using yarn:

```bash
cd frontend
yarn install
```

### 2. Environment Configuration (Optional)

Create a `.env` file in the frontend directory if you need to customize the API URL:

```bash
REACT_APP_API_URL=http://localhost:8000
```

The default API URL is `http://localhost:8000`, which should work if you're running the backend locally.

### 3. Start Development Server

```bash
npm start
```

Or using yarn:

```bash
yarn start
```

The application will open in your browser at [http://localhost:3000](http://localhost:3000).

## Building for Production

```bash
npm run build
```

This creates an optimized production build in the `build` folder.

## Architecture

```
src/
├── components/           # React components
│   ├── Chat.js          # Main chat interface
│   ├── Message.js       # Individual message display
│   └── SystemStatus.js  # System health status
├── api/                 # API communication layer
│   └── activityApi.js   # Backend API calls
├── styles/              # CSS styling
│   ├── index.css        # Global styles
│   └── App.css          # Application-specific styles
├── App.js               # Main application component
└── index.js             # Application entry point
```

## Components

### Chat Component
- Handles user input and message history
- Provides quick query buttons for common requests
- Manages loading states and error handling

### Message Component
- Displays individual messages with timestamps
- Shows detailed JIRA and GitHub data when available
- Expandable details with rich formatting

### SystemStatus Component
- Real-time monitoring of backend health
- Shows JIRA and GitHub connection status
- Provides helpful configuration guidance

## API Integration

The frontend communicates with the backend through a comprehensive API client that handles:

- Team activity queries with natural language processing
- System status monitoring
- Individual JIRA and GitHub data requests
- Error handling and retry logic

## Styling

The application uses:
- Custom CSS with modern design patterns
- Responsive grid layouts
- Smooth animations and transitions
- Color-coded status indicators
- Mobile-first responsive design

## Usage Examples

### Basic Queries
- "What has the team been working on this week?"
- "Show me recent GitHub activity"
- "What JIRA issues are in progress?"

### Team-Specific Queries
- "What has @john been working on?"
- "Show me commits by sarah in the last 5 days"
- "Recent pull requests by team members"

### Project/Repository Specific
- "GitHub activity in the frontend repo"
- "Issues in project ABC"
- "Commits in the backend repository"

## Features

### Quick Queries
Pre-defined query buttons for common requests to help users get started quickly.

### System Health Monitoring
Visual indicators showing the health of JIRA and GitHub integrations with helpful configuration tips.

### Rich Data Display
- JIRA issues with status badges and assignee information
- GitHub commits with repository and author details
- Pull requests with merge status and metadata
- Expandable details for comprehensive information

### Responsive Design
The interface adapts to different screen sizes:
- Desktop: Full-width layout with side-by-side components
- Tablet: Adjusted layout with collapsible elements
- Mobile: Stacked layout with touch-friendly interactions

## Error Handling

The frontend provides comprehensive error handling:
- Network errors with retry suggestions
- API errors with detailed messages
- Configuration issues with setup guidance
- Loading states with clear feedback

## Development

### Available Scripts

- `npm start` - Start development server
- `npm run build` - Build for production
- `npm test` - Run test suite
- `npm run eject` - Eject from Create React App

### Code Structure

- Components are functional React components using hooks
- API calls are centralized in the `api` directory
- Styling follows BEM methodology with CSS modules
- Error boundaries protect against component crashes

## Browser Support

- Chrome (last 2 versions)
- Firefox (last 2 versions)
- Safari (last 2 versions)
- Edge (last 2 versions)

## Troubleshooting

### Common Issues

1. **Backend Connection Error**
   - Ensure the backend is running on port 8000
   - Check the REACT_APP_API_URL environment variable

2. **CORS Issues**
   - The backend is configured to allow requests from localhost:3000
   - If running on a different port, update the backend CORS settings

3. **Build Issues**
   - Clear node_modules and package-lock.json, then reinstall
   - Ensure Node.js version is 16 or higher
