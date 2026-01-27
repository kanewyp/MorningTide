import React from 'react';
import Chatbot from '../components/Chatbot/Chatbot';
import './ChatBotPage.css';

const ChatBotPage = () => {
    return (
        <div className="chatbot-page">
            <div className="chatbot-page-background">
                <div className="background-circle circle-1"></div>
                <div className="background-circle circle-2"></div>
                <div className="background-circle circle-3"></div>
            </div>

            <div className="chatbot-page-content">
                <Chatbot />
            </div>
        </div>
    );
};

export default ChatBotPage;