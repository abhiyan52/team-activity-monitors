const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

const handleResponse = async (response) => {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new ApiError(
      errorData.detail || `HTTP error! status: ${response.status}`,
      response.status
    );
  }
  return response.json();
};

export const queryTeamActivity = async (query, teamMembers = null, dateRange = null) => {
  const requestBody = {
    query,
    team_members: teamMembers,
    date_range: dateRange
  };

  const response = await fetch(`${API_BASE_URL}/api/activity/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(requestBody)
  });

  return handleResponse(response);
};

export const getSystemStatus = async () => {
  const response = await fetch(`${API_BASE_URL}/api/activity/status`);
  return handleResponse(response);
};

export const getRecentSummary = async (days = 7) => {
  const response = await fetch(`${API_BASE_URL}/api/activity/recent-summary?days=${days}`);
  return handleResponse(response);
};

export const parseQuery = async (query) => {
  const response = await fetch(`${API_BASE_URL}/api/activity/parse-query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(query)
  });
  return handleResponse(response);
};

// JIRA API functions
export const getJiraHealth = async () => {
  const response = await fetch(`${API_BASE_URL}/api/jira/health`);
  return handleResponse(response);
};

export const getJiraIssues = async (filters = {}) => {
  const queryParams = new URLSearchParams();
  
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== '') {
      if (Array.isArray(value)) {
        value.forEach(v => queryParams.append(key, v));
      } else {
        queryParams.append(key, value);
      }
    }
  });

  const response = await fetch(`${API_BASE_URL}/api/jira/issues?${queryParams}`);
  return handleResponse(response);
};

export const getJiraRecentActivity = async (days = 7, teamMembers = null) => {
  const queryParams = new URLSearchParams({ days: days.toString() });
  
  if (teamMembers && teamMembers.length > 0) {
    teamMembers.forEach(member => queryParams.append('team_members', member));
  }

  const response = await fetch(`${API_BASE_URL}/api/jira/recent-activity?${queryParams}`);
  return handleResponse(response);
};

// GitHub API functions
export const getGitHubHealth = async () => {
  const response = await fetch(`${API_BASE_URL}/api/github/health`);
  return handleResponse(response);
};

export const getGitHubRepositories = async () => {
  const response = await fetch(`${API_BASE_URL}/api/github/repositories`);
  return handleResponse(response);
};

export const getGitHubCommits = async (filters = {}) => {
  const queryParams = new URLSearchParams();
  
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== '') {
      if (Array.isArray(value)) {
        value.forEach(v => queryParams.append(key, v));
      } else {
        queryParams.append(key, value);
      }
    }
  });

  const response = await fetch(`${API_BASE_URL}/api/github/commits?${queryParams}`);
  return handleResponse(response);
};

export const getGitHubPullRequests = async (filters = {}) => {
  const queryParams = new URLSearchParams();
  
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== '') {
      if (Array.isArray(value)) {
        value.forEach(v => queryParams.append(key, v));
      } else {
        queryParams.append(key, value);
      }
    }
  });

  const response = await fetch(`${API_BASE_URL}/api/github/pull-requests?${queryParams}`);
  return handleResponse(response);
};

export const getGitHubRecentActivity = async (days = 7, teamMembers = null, repositories = null) => {
  const queryParams = new URLSearchParams({ days: days.toString() });
  
  if (teamMembers && teamMembers.length > 0) {
    teamMembers.forEach(member => queryParams.append('team_members', member));
  }
  
  if (repositories && repositories.length > 0) {
    repositories.forEach(repo => queryParams.append('repositories', repo));
  }

  const response = await fetch(`${API_BASE_URL}/api/github/recent-activity?${queryParams}`);
  return handleResponse(response);
};

export const getGitHubUser = async () => {
  const response = await fetch(`${API_BASE_URL}/api/github/user`);
  return handleResponse(response);
};
