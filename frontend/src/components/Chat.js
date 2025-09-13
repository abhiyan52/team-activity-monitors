import React, { useState, useRef, useEffect } from 'react';
import Message from './Message';
import { queryTeamActivity } from '../api/activityApi';

const Chat = ({ systemStatus }) => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'assistant',
      content: 'Hi! I can help you track your team\'s activity across JIRA and GitHub. Try asking me something like "What has the team been working on this week?" or "Show me recent commits by @john".',
      timestamp: new Date()
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputValue,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await queryTeamActivity(inputValue);
      
      const assistantMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: response.summary_text,
        data: {
          jira: response.jira,
          github: response.github,
          query_metadata: response.query_metadata
        },
        timestamp: new Date(response.generated_at)
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error querying activity:', error);
      
      const errorMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: `Sorry, I encountered an error: ${error.message}. Please check that the backend is running and properly configured.`,
        timestamp: new Date(),
        isError: true
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickQuery = (query) => {
    setInputValue(query);
  };

  const quickQueries = [
    "What has the team been working on this week?",
    "Show me recent GitHub activity",
    "What JIRA issues are in progress?",
    "Recent commits by team members",
    "Show me pull requests from last week"
  ];

  const isSystemHealthy = systemStatus?.overall_status === 'healthy';

  return (
    <div className="chat-container">
      <div className="chat-messages">
        {messages.map(message => (
          <Message key={message.id} message={message} />
        ))}
        {isLoading && (
          <div className="loading-message">
            <div className="loading-spinner"></div>
            <span>Analyzing team activity...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {!isSystemHealthy && (
        <div className="system-warning">
          ⚠️ System not fully configured. Some features may not work properly.
        </div>
      )}

      <div className="quick-queries">
        <h4>Try asking:</h4>
        <div className="quick-query-buttons">
          {quickQueries.map((query, index) => (
            <button
              key={index}
              onClick={() => handleQuickQuery(query)}
              className="quick-query-button"
              disabled={isLoading}
            >
              {query}
            </button>
          ))}
        </div>
      </div>

      <form onSubmit={handleSubmit} className="chat-input-form">
        <div className="chat-input-container">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Ask me about your team's activity..."
            className="chat-input"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!inputValue.trim() || isLoading}
            className="chat-submit-button"
          >
            {isLoading ? '...' : 'Send'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default Chat;
