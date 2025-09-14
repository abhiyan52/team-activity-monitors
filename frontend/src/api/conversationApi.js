/**
 * Conversation API client for Team Activity Monitor
 * All queries should go through the intelligent agent via conversation API
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

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

// Conversation API functions
export const createConversationThread = async (title = null) => {
  const response = await fetch(`${API_BASE_URL}/api/conversations/threads`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ title })
  });
  return handleResponse(response);
};

export const listConversationThreads = async (limit = 50, offset = 0) => {
  const response = await fetch(`${API_BASE_URL}/api/conversations/threads?limit=${limit}&offset=${offset}`);
  return handleResponse(response);
};

export const getConversationThread = async (threadId) => {
  const response = await fetch(`${API_BASE_URL}/api/conversations/threads/${threadId}`);
  return handleResponse(response);
};

export const sendMessage = async (threadId, content) => {
  const response = await fetch(`${API_BASE_URL}/api/conversations/threads/${threadId}/messages`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ content })
  });
  return handleResponse(response);
};

export const getConversationHistory = async (threadId) => {
  const response = await fetch(`${API_BASE_URL}/api/conversations/threads/${threadId}/history`);
  return handleResponse(response);
};

export const getConversationMessages = async (threadId, limit = 100, offset = 0) => {
  const response = await fetch(`${API_BASE_URL}/api/conversations/threads/${threadId}/messages?limit=${limit}&offset=${offset}`);
  return handleResponse(response);
};

export const updateThreadTitle = async (threadId, title) => {
  const response = await fetch(`${API_BASE_URL}/api/conversations/threads/${threadId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ title })
  });
  return handleResponse(response);
};

export const deleteThread = async (threadId) => {
  const response = await fetch(`${API_BASE_URL}/api/conversations/threads/${threadId}`, {
    method: 'DELETE',
  });
  return response.ok;
};

export const clearAgentMemory = async (threadId) => {
  const response = await fetch(`${API_BASE_URL}/api/conversations/threads/${threadId}/clear-memory`, {
    method: 'POST',
  });
  return handleResponse(response);
};

// Convenience function for querying team activity through the agent
export const queryTeamActivity = async (query, threadId = null) => {
  // If no thread ID provided, create a new thread
  if (!threadId) {
    const thread = await createConversationThread(`Query: ${query.substring(0, 50)}...`);
    threadId = thread.id;
  }
  
  // Send the query to the agent
  const response = await sendMessage(threadId, query);
  
  return {
    ...response,
    threadId: threadId
  };
};

// Health check
export const getSystemStatus = async () => {
  const response = await fetch(`${API_BASE_URL}/health`);
  return handleResponse(response);
};

export default {
  createConversationThread,
  listConversationThreads,
  getConversationThread,
  sendMessage,
  getConversationHistory,
  getConversationMessages,
  updateThreadTitle,
  deleteThread,
  clearAgentMemory,
  queryTeamActivity,
  getSystemStatus
};
