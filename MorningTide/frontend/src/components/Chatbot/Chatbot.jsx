import React, { useState, useRef, useEffect } from 'react';
import './Chatbot.css';

const Chatbot = () => {
    const [messages, setMessages] = useState([
        {
            id: 1,
            type: 'bot',
            content: 'Hello! I\'m here to help you prepare for your therapy session. I can analyze your recent journal entries and suggest meaningful discussion topics. How can I assist you today?',
            timestamp: new Date()
        }
    ]);
    const [inputMessage, setInputMessage] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [diaryEntries, setDiaryEntries] = useState([]);
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    useEffect(() => {
        fetchRecentDiaryEntries();
    }, []);

    const fetchRecentDiaryEntries = async () => {
        const token = localStorage.getItem('token');
        if (!token) return;

        const response = await fetch('http://localhost:8000/api/journal/entries', {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            const data = await response.json();
            // The API returns an array directly, not { entries: [...] }
            setDiaryEntries(Array.isArray(data) ? data : []);
        }
    };

    const handleSendMessage = async (e) => {
        e.preventDefault();

        if (!inputMessage.trim()) return;

        const userMessage = {
            id: Date.now(),
            type: 'user',
            content: inputMessage,
            timestamp: new Date()
        };

        setMessages(prev => [...prev, userMessage]);
        const currentInput = inputMessage;
        setInputMessage('');
        setIsLoading(true);

        const isTherapyRequest =
            currentInput.toLowerCase().includes('suggest') ||
            currentInput.toLowerCase().includes('therapy') ||
            currentInput.toLowerCase().includes('discuss') ||
            currentInput.toLowerCase().includes('session') ||
            currentInput.toLowerCase().includes('help') ||
            currentInput.toLowerCase().includes('analyze');

        if (diaryEntries.length === 0) {
            setMessages(prev => [...prev, {
                id: Date.now() + 1,
                type: 'bot',
                content: 'I notice you haven\'t written any journal entries yet. To provide personalized therapy suggestions, I need to understand your recent thoughts and feelings. Would you like to write your first journal entry?',
                timestamp: new Date()
            }]);
            setIsLoading(false);
            return;
        }

        if (isTherapyRequest) {
            await generateTherapySuggestions();
        } else {
            await retrieveTopics(currentInput);
        }

        setIsLoading(false);
    };

    const generateTherapySuggestions = async () => {
        const token = localStorage.getItem('token');

        const response = await fetch('http://localhost:8000/api/rag/generate-suggestions', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                diary_entries: diaryEntries.map(entry => ({
                    date: entry.date,
                    content: entry.content
                })),
                top_k: 5,
                stream: false
            })
        });

        const data = await response.json();

        if (response.ok && data.status === 'success') {
            setMessages(prev => [...prev, {
                id: Date.now() + 1,
                type: 'bot',
                content: formatTherapySuggestions(data),
                timestamp: new Date()
            }]);
        } else {
            setMessages(prev => [...prev, {
                id: Date.now() + 1,
                type: 'bot',
                content: 'I\'m having trouble generating suggestions right now. Please try again in a moment.',
                timestamp: new Date()
            }]);
        }
    };

    const retrieveTopics = async (query) => {
        const token = localStorage.getItem('token');

        const response = await fetch('http://localhost:8000/api/rag/retrieve-topics', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: query,
                top_k: 3
            })
        });

        const data = await response.json();

        if (response.ok && data.status === 'success') {
            setMessages(prev => [...prev, {
                id: Date.now() + 1,
                type: 'bot',
                content: formatTopics(data.topics),
                timestamp: new Date()
            }]);
        } else {
            setMessages(prev => [...prev, {
                id: Date.now() + 1,
                type: 'bot',
                content: 'I couldn\'t find relevant topics for your query. Could you rephrase or ask something else?',
                timestamp: new Date()
            }]);
        }
    };

    const formatTherapySuggestions = (data) => {
        const analysis = data.diary_analysis || {};
        const entryCount = analysis.entry_count || diaryEntries.length;
        const themes = analysis.themes || [];

        let formatted = `Based on your recent ${entryCount} journal ${entryCount === 1 ? 'entry' : 'entries'}`;

        if (themes.length > 0) {
            formatted += `, I've identified these themes: ${themes.join(', ')}.`;
        }

        formatted += '\n\n' + (data.suggestions || 'No specific suggestions available at this time.');

        return formatted;
    };

    const formatTopics = (topics) => {
        if (!topics || topics.length === 0) {
            return 'I couldn\'t find specific topics related to your query, but I\'m here to help. Could you provide more details?';
        }

        let formatted = 'Here are some relevant therapy topics that might help:\n\n';

        topics.forEach((topic, index) => {
            formatted += `${index + 1}. **${topic.title || 'Untitled'}**\n`;
            if (topic.content) {
                formatted += `   ${topic.content.substring(0, 150)}...\n`;
            }
            if (topic.similarity_score) {
                formatted += `   (Relevance: ${(topic.similarity_score * 100).toFixed(0)}%)\n\n`;
            }
        });

        return formatted;
    };

    const handleQuickAction = (action) => {
        const quickMessages = {
            suggest: 'Can you suggest discussion topics for my next therapy session?',
            analyze: 'Can you analyze my recent journal entries?',
            anxiety: 'I want to talk about anxiety management techniques',
            mood: 'How has my mood been recently?'
        };

        setInputMessage(quickMessages[action]);

        setTimeout(() => {
            inputRef.current?.form.requestSubmit();
        }, 100);
    };

    const formatTimestamp = (date) => {
        return new Date(date).toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    return (
        <div className="chatbot-container">
            <div className="chatbot-header">
                <div className="header-content">
                    <div className="bot-avatar">
                        <span className="bot-icon">🌸</span>
                    </div>
                    <div className="header-text">
                        <h2>Therapy Assistant</h2>
                        <p className="status">
                            <span className="status-dot"></span>
                            Ready to help
                        </p>
                    </div>
                </div>
            </div>

            <div className="chatbot-messages">
                {messages.map((message) => (
                    <div
                        key={message.id}
                        className={`message ${message.type === 'user' ? 'message-user' : 'message-bot'}`}
                    >
                        {message.type === 'bot' && (
                            <div className="message-avatar">
                                <span className="avatar-icon">🌸</span>
                            </div>
                        )}

                        <div className="message-content">
                            <div className="message-bubble">
                                {message.content.split('\n').map((line, index) => {
                                    const parts = line.split(/(\*\*.*?\*\*)/g);
                                    return (
                                        <p key={index}>
                                            {parts.map((part, i) => {
                                                if (part.startsWith('**') && part.endsWith('**')) {
                                                    return <strong key={i}>{part.slice(2, -2)}</strong>;
                                                }
                                                return part;
                                            })}
                                        </p>
                                    );
                                })}
                            </div>
                            <span className="message-time">{formatTimestamp(message.timestamp)}</span>
                        </div>

                        {message.type === 'user' && (
                            <div className="message-avatar">
                                <span className="avatar-icon">👤</span>
                            </div>
                        )}
                    </div>
                ))}

                {isLoading && (
                    <div className="message message-bot">
                        <div className="message-avatar">
                            <span className="avatar-icon">🌸</span>
                        </div>
                        <div className="message-content">
                            <div className="message-bubble typing-indicator">
                                <span></span>
                                <span></span>
                                <span></span>
                            </div>
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {messages.length === 1 && !isLoading && (
                <div className="quick-actions">
                    <p className="quick-actions-title">Quick actions:</p>
                    <div className="quick-actions-grid">
                        <button
                            className="quick-action-btn"
                            onClick={() => handleQuickAction('suggest')}
                        >
                            <span className="quick-action-icon">💭</span>
                            Suggest Topics
                        </button>
                        <button
                            className="quick-action-btn"
                            onClick={() => handleQuickAction('analyze')}
                        >
                            <span className="quick-action-icon">📊</span>
                            Analyze Entries
                        </button>
                        <button
                            className="quick-action-btn"
                            onClick={() => handleQuickAction('anxiety')}
                        >
                            <span className="quick-action-icon">🧘</span>
                            Anxiety Help
                        </button>
                        <button
                            className="quick-action-btn"
                            onClick={() => handleQuickAction('mood')}
                        >
                            <span className="quick-action-icon">😊</span>
                            Mood Patterns
                        </button>
                    </div>
                </div>
            )}

            <div className="chatbot-input-container">
                <form onSubmit={handleSendMessage} className="chatbot-input-form">
                    <input
                        ref={inputRef}
                        type="text"
                        value={inputMessage}
                        onChange={(e) => setInputMessage(e.target.value)}
                        placeholder="Ask me anything about your therapy journey..."
                        className="chatbot-input"
                        disabled={isLoading}
                    />
                    <button
                        type="submit"
                        className="send-button"
                        disabled={isLoading || !inputMessage.trim()}
                    >
                        <svg
                            width="20"
                            height="20"
                            viewBox="0 0 20 20"
                            fill="none"
                            xmlns="http://www.w3.org/2000/svg"
                        >
                            <path
                                d="M2 10L18 2L10 18L8 11L2 10Z"
                                stroke="currentColor"
                                strokeWidth="2"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                fill="currentColor"
                            />
                        </svg>
                    </button>
                </form>
                <p className="input-hint">
                    Ask for therapy suggestions, discuss your feelings, or explore coping strategies
                </p>
            </div>
        </div>
    );
};

export default Chatbot;