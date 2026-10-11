import React, { useState, useRef, useEffect } from 'react';
import { journalAPI, ragAPI } from '../../services/api';
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
    const [diaryLoadError, setDiaryLoadError] = useState('');
    const [ragStatus, setRagStatus] = useState('Checking local model...');
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    useEffect(() => {
        fetchRecentDiaryEntries();
        checkRagHealth();
    }, []);

    const fetchRecentDiaryEntries = async () => {
        try {
            const response = await journalAPI.getEntries();
            setDiaryEntries(Array.isArray(response.data) ? response.data : []);
            setDiaryLoadError('');
        } catch (error) {
            setDiaryLoadError(
                error.response?.data?.message || error.message || 'Could not load journal entries.'
            );
        }
    };

    const checkRagHealth = async () => {
        try {
            const response = await ragAPI.health();
            const generator = response.data.generator || {};
            if (generator.status === 'healthy' && generator.model_available) {
                setRagStatus('Local model ready');
            } else if (generator.error) {
                setRagStatus('Ollama offline');
            } else {
                setRagStatus('Configured model not found');
            }
        } catch (error) {
            setRagStatus(error.response?.status === 503 ? 'RAG unavailable' : 'API unavailable');
        }
    };

    const sendMessage = async (messageText) => {
        const currentInput = messageText.trim();
        if (!currentInput || isLoading) return;

        const userMessage = {
            id: Date.now(),
            type: 'user',
            content: currentInput,
            timestamp: new Date()
        };

        setMessages(prev => [...prev, userMessage]);
        setInputMessage('');
        setIsLoading(true);

        if (diaryEntries.length === 0) {
            setMessages(prev => [...prev, {
                id: Date.now() + 1,
                type: 'bot',
                content: diaryLoadError
                    ? `I could not load your journal entries: ${diaryLoadError}`
                    : 'I notice you haven\'t written any journal entries yet. Write a journal entry first and I can use it to personalize this conversation.',
                timestamp: new Date()
            }]);
            setIsLoading(false);
            return;
        }

        await generateTherapySuggestions(currentInput);
        setIsLoading(false);
    };

    const handleSendMessage = (event) => {
        event.preventDefault();
        sendMessage(inputMessage);
    };

    const generateTherapySuggestions = async (question) => {
        try {
            const response = await ragAPI.generateSuggestions({
                diary_entries: diaryEntries.slice(0, 10).map(entry => ({
                    date: entry.date,
                    content: entry.content
                })),
                top_k: 5,
                stream: false,
                question,
            });
            const data = response.data;
            setMessages(prev => [...prev, {
                id: Date.now() + 1,
                type: 'bot',
                content: formatTherapySuggestions(data),
                timestamp: new Date()
            }]);
        } catch (error) {
            const message = error.response?.data?.error || error.message || 'Check that the API and Ollama are running.';
            setMessages(prev => [...prev, {
                id: Date.now() + 1,
                type: 'bot',
                content: `I could not generate a response. ${message}`,
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

    const handleQuickAction = (action) => {
        const quickMessages = {
            suggest: 'Can you suggest discussion topics for my next therapy session?',
            analyze: 'Can you analyze my recent journal entries?',
            anxiety: 'I want to talk about anxiety management techniques',
            mood: 'How has my mood been recently?'
        };

        sendMessage(quickMessages[action]);
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
                            {isLoading ? 'Preparing a response...' : diaryLoadError ? 'Journal unavailable' : ragStatus}
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