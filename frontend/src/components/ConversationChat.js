import React, { useState, useEffect, useRef } from 'react';
import {
  createConversationThread,
  listConversationThreads,
  sendMessage,
  getConversationHistory,
  updateThreadTitle,
  deleteThread
} from '../api/conversationApi';

const ConversationChat = () => {
  const [currentThread, setCurrentThread] = useState(null);
  const [messages, setMessages] = useState([]);
  const [threads, setThreads] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    loadThreads();
  }, []);

  const loadThreads = async () => {
    try {
      const threadList = await listConversationThreads();
      setThreads(threadList);
    } catch (error) {
      setError('Failed to load conversations');
      console.error('Error loading threads:', error);
    }
  };

  const createNewThread = async (title = null) => {
    try {
      const thread = await createConversationThread(title);
      setCurrentThread(thread);
      setMessages([]);
      await loadThreads(); // Refresh thread list
      return thread;
    } catch (error) {
      setError('Failed to create new conversation');
      console.error('Error creating thread:', error);
      throw error;
    }
  };

  const loadThread = async (threadId) => {
    try {
      setLoading(true);
      const history = await getConversationHistory(threadId);
      setCurrentThread(history.thread);
      setMessages(history.messages);
    } catch (error) {
      setError('Failed to load conversation');
      console.error('Error loading thread:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || loading) return;

    const content = inputValue.trim();
    setInputValue('');
    setError(null);

    try {
      setLoading(true);

      // Create thread if none exists
      let thread = currentThread;
      if (!thread) {
        thread = await createNewThread(`Query: ${content.substring(0, 30)}...`);
      }

      // Add user message to UI immediately
      const userMessage = {
        id: `temp-${Date.now()}`,
        thread_id: thread.id,
        role: 'user',
        content,
        created_at: new Date().toISOString(),
      };
      setMessages(prev => [...prev, userMessage]);

      // Send to agent
      const response = await sendMessage(thread.id, content);

      // Add agent response to UI
      const agentMessage = {
        id: response.assistant_message_id,
        thread_id: thread.id,
        role: 'assistant',
        content: response.response,
        created_at: new Date().toISOString(),
        processing_time: response.processing_time,
      };

      setMessages(prev => [
        ...prev.filter(msg => msg.id !== userMessage.id),
        {
          ...userMessage,
          id: response.user_message_id,
        },
        agentMessage,
      ]);

    } catch (error) {
      setError(`Failed to send message: ${error.message}`);
      // Remove temporary user message on error
      setMessages(prev => prev.filter(msg => msg.id !== `temp-${Date.now()}`));
    } finally {
      setLoading(false);
    }
  };

  const handleThreadSelect = (thread) => {
    loadThread(thread.id);
  };

  const handleDeleteThread = async (threadId, e) => {
    e.stopPropagation();
    try {
      await deleteThread(threadId);
      await loadThreads();
      if (currentThread && currentThread.id === threadId) {
        setCurrentThread(null);
        setMessages([]);
      }
    } catch (error) {
      setError('Failed to delete conversation');
    }
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div style={{ display: 'flex', height: '100vh', fontFamily: 'Arial, sans-serif' }}>
      {/* Sidebar */}
      <div style={{ 
        width: '300px', 
        borderRight: '1px solid #e1e5e9', 
        backgroundColor: '#f8f9fa',
        display: 'flex',
        flexDirection: 'column'
      }}>
        <div style={{ padding: '20px', borderBottom: '1px solid #e1e5e9' }}>
          <h3 style={{ margin: '0 0 15px 0' }}>Team Activity Monitor</h3>
          <button 
            onClick={() => createNewThread()}
            style={{
              width: '100%',
              padding: '10px',
              backgroundColor: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
            disabled={loading}
          >
            + New Conversation
          </button>
        </div>

        <div style={{ flex: 1, overflow: 'auto', padding: '10px' }}>
          {threads.map(thread => (
            <div
              key={thread.id}
              onClick={() => handleThreadSelect(thread)}
              style={{
                padding: '12px',
                margin: '5px 0',
                cursor: 'pointer',
                backgroundColor: currentThread?.id === thread.id ? '#e3f2fd' : 'white',
                border: '1px solid #e1e5e9',
                borderRadius: '6px',
                position: 'relative'
              }}
            >
              <div style={{ 
                fontWeight: currentThread?.id === thread.id ? 'bold' : 'normal',
                fontSize: '14px',
                marginBottom: '4px'
              }}>
                {thread.title}
              </div>
              <div style={{ 
                fontSize: '12px', 
                color: '#6c757d',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}>
                <span>{thread.message_count} messages</span>
                <button
                  onClick={(e) => handleDeleteThread(thread.id, e)}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: '#dc3545',
                    cursor: 'pointer',
                    fontSize: '12px'
                  }}
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Chat Area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {currentThread ? (
          <>
            {/* Header */}
            <div style={{ 
              padding: '20px', 
              borderBottom: '1px solid #e1e5e9',
              backgroundColor: 'white'
            }}>
              <h2 style={{ margin: 0, fontSize: '18px' }}>{currentThread.title}</h2>
              <p style={{ margin: '5px 0 0 0', color: '#6c757d', fontSize: '14px' }}>
                Ask about team activity, JIRA tickets, GitHub commits, or any project-related questions
              </p>
            </div>

            {/* Messages */}
            <div style={{ 
              flex: 1, 
              overflow: 'auto', 
              padding: '20px',
              backgroundColor: '#f8f9fa'
            }}>
              {messages.map(message => (
                <div
                  key={message.id}
                  style={{
                    marginBottom: '20px',
                    display: 'flex',
                    justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start'
                  }}
                >
                  <div style={{
                    maxWidth: '70%',
                    padding: '12px 16px',
                    borderRadius: '18px',
                    backgroundColor: message.role === 'user' ? '#007bff' : 'white',
                    color: message.role === 'user' ? 'white' : '#333',
                    border: message.role === 'assistant' ? '1px solid #e1e5e9' : 'none',
                    whiteSpace: 'pre-wrap'
                  }}>
                    <div>{message.content}</div>
                    <div style={{ 
                      fontSize: '11px', 
                      marginTop: '8px',
                      opacity: 0.7,
                      display: 'flex',
                      justifyContent: 'space-between'
                    }}>
                      <span>{formatTime(message.created_at)}</span>
                      {message.processing_time && (
                        <span>{message.processing_time}ms</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              {loading && (
                <div style={{ textAlign: 'center', color: '#6c757d' }}>
                  <div>🤔 Agent is thinking...</div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <form onSubmit={handleSendMessage} style={{ 
              padding: '20px', 
              borderTop: '1px solid #e1e5e9',
              backgroundColor: 'white'
            }}>
              {error && (
                <div style={{ 
                  marginBottom: '10px',
                  padding: '10px',
                  backgroundColor: '#f8d7da',
                  color: '#721c24',
                  borderRadius: '6px',
                  fontSize: '14px'
                }}>
                  {error}
                </div>
              )}
              <div style={{ display: 'flex', gap: '10px' }}>
                <input
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="Ask about team activity, tickets, commits, or anything..."
                  style={{ 
                    flex: 1, 
                    padding: '12px 16px',
                    border: '1px solid #e1e5e9',
                    borderRadius: '25px',
                    fontSize: '14px',
                    outline: 'none'
                  }}
                  disabled={loading}
                />
                <button
                  type="submit"
                  disabled={loading || !inputValue.trim()}
                  style={{
                    padding: '12px 24px',
                    backgroundColor: '#007bff',
                    color: 'white',
                    border: 'none',
                    borderRadius: '25px',
                    cursor: loading || !inputValue.trim() ? 'not-allowed' : 'pointer',
                    fontSize: '14px',
                    opacity: loading || !inputValue.trim() ? 0.6 : 1
                  }}
                >
                  {loading ? 'Sending...' : 'Send'}
                </button>
              </div>
            </form>
          </>
        ) : (
          <div style={{ 
            flex: 1, 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            textAlign: 'center',
            backgroundColor: '#f8f9fa'
          }}>
            <div>
              <h3 style={{ color: '#6c757d' }}>Welcome to Team Activity Monitor</h3>
              <p style={{ color: '#6c757d', marginBottom: '20px' }}>
                Start a new conversation or select an existing one to begin asking about your team's activity.
              </p>
              <button 
                onClick={() => createNewThread()}
                style={{
                  padding: '12px 24px',
                  backgroundColor: '#007bff',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '16px'
                }}
                disabled={loading}
              >
                Start New Conversation
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ConversationChat;
