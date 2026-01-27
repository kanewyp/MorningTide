import React from 'react';
import { motion } from 'framer-motion';
import './Diary.css';

const EmotionResult = ({ analysis }) => {
    // HELPER FUNCTION:  Returns color based on score
    const getScoreColor = (score) => {
        if (score <= 3) return '#9BA8B8';  // Negative
        if (score <= 7) return '#B8C9D9';  // Neutral
        return '#7EC4CF';                  // Positive
    };

    // HELPER FUNCTION: Returns label based on score
    const getScoreLabel = (score) => {
        if (score <= 3) return 'Challenging';
        if (score <= 4) return 'Low';
        if (score <= 6) return 'Moderate';
        if (score <= 7) return 'Good';
        if (score <= 9) return 'Great';
        return 'Excellent';
    };

    // EMOTION EMOJI MAPPING - makes it visual
    const emotionEmojis = {
        joy: '😊',
        happiness: '😄',
        love: '❤️',
        excitement: '🎉',
        calm: '😌',
        peaceful: '☮️',
        content: '😊',
        gratitude: '🙏',
        sadness: '😢',
        anger: '😠',
        fear: '😰',
        anxiety: '😟',
        frustration: '😤',
        disappointment: '😞',
        loneliness: '😔',
        confusion: '😕',
        surprise: '😲',
        hope: '🌟',
        pride: '🌟'
    };

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="emotion-result card"
        >
            <h3 className="result-title">Your Emotional Landscape</h3>

            {/* CIRCULAR SCORE DISPLAY */}
            <div className="emotion-score-container">
                <div className="score-circle" style={{
                    // CONIC GRADIENT - creates pie chart effect
                    background: `conic-gradient(
            ${getScoreColor(analysis.emotion_score)} ${analysis.emotion_score * 10}%, 
            #E8F2F7 0
          )`
                }}>
                    <div className="score-inner">
                        <div className="score-value">{analysis.emotion_score}</div>
                        <div className="score-label">{getScoreLabel(analysis.emotion_score)}</div>
                    </div>
                </div>

                <div className="score-description">
                    <p>Your emotional intensity today</p>
                    <div className="score-scale">
                        <span>1 - Strongly Negative  </span>
                        <span>5 - Neutral  </span>
                        <span>10 - Strongly Positive</span>
                    </div>
                </div>
            </div>

            {/* TOP 3 EMOTIONS */}
            <div className="top-emotions">
                <h4>Top 3 Emotions Detected</h4>
                <div className="emotions-grid">
                    {analysis.top_emotions.map((emotion, index) => (
                        <motion.div
                            key={index}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: index * 0.1 }}  // Stagger animation
                            className="emotion-card"
                        >
                            {/* RANK BADGE */}
                            <div className="emotion-rank">#{index + 1}</div>

                            {/* EMOJI */}
                            <div className="emotion-emoji">
                                {emotionEmojis[emotion.emotion.toLowerCase()] || '💭'}
                            </div>

                            {/* EMOTION NAME */}
                            <div className="emotion-name">{emotion.emotion}</div>

                            {/* CONFIDENCE PERCENTAGE */}
                            <div className="emotion-confidence">
                                {(emotion.probability * 100).toFixed(1)}% confidence
                            </div>

                            {/* PROGRESS BAR */}
                            <div className="emotion-bar">
                                <div
                                    className="emotion-bar-fill"
                                    style={{
                                        width: `${emotion.probability * 100}%`,
                                        background: getScoreColor(analysis.emotion_score)
                                    }}
                                />
                            </div>
                        </motion.div>
                    ))}
                </div>
            </div>

            {/* TIMESTAMP */}
            <div className="analysis-timestamp">
                Analyzed on {new Date(analysis.analyzed_at).toLocaleString()}
            </div>
        </motion.div>
    );
};

export default EmotionResult;