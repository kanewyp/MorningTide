import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import Calendar from 'react-calendar';
import 'react-calendar/dist/Calendar.css';
import { journalAPI } from '../../services/api';
import './EmotionCalendar.css';

const EmotionCalendar = () => {
    const [date, setDate] = useState(new Date());
    const [entriesMap, setEntriesMap] = useState({});  // Object:  { "2026-01-12": entry }
    const [selectedEntry, setSelectedEntry] = useState(null);
    const [loading, setLoading] = useState(true);

    // EFFECT:  Fetch entries when month changes
    useEffect(() => {
        fetchMonthEntries(date);
    }, [date]);  // Re-run when date changes

    const fetchMonthEntries = async (currentDate) => {
        setLoading(true);
        try {
            // Calculate month boundaries
            const year = currentDate.getFullYear();
            const month = currentDate.getMonth();
            const startDate = new Date(year, month, 1).toISOString().split('T')[0];  // First day
            const endDate = new Date(year, month + 1, 0).toISOString().split('T')[0];  // Last day

            const response = await journalAPI.getEntries(startDate, endDate);
            const entries = response.data;

            // TRANSFORM ARRAY TO OBJECT for O(1) lookup
            // Instead of: entries.find(e => e.date === "2026-01-12")  // O(n)
            // We do: entriesMap["2026-01-12"]  // O(1)
            const map = {};
            for (const entry of entries) {
                if (entry.analysis) {  // Only include analyzed entries
                    map[entry.date] = {
                        ...entry,
                        analysis: entry.analysis
                    };
                }
            }
            setEntriesMap(map);

        } catch (error) {
            console.error('Failed to fetch entries:', error);
        } finally {
            setLoading(false);
        }
    };

    // CUSTOM TILE CONTENT - what shows on each calendar day
    const getTileContent = ({ date, view }) => {
        if (view === 'month') {
            const dateStr = date.toISOString().split('T')[0];
            const entry = entriesMap[dateStr];  // O(1) lookup!

            if (entry && entry.analysis) {
                const score = entry.analysis.emotion_score;

                return (
                    <div className="calendar-tile-content">
                        {/* Show 3 dots for top 3 emotions */}
                        <div className="tile-emotions">
                            {entry.analysis.top_emotions.slice(0, 3).map((e, i) => (
                                <span
                                    key={i}
                                    className="tile-emotion-dot"
                                    style={{ background: getScoreColor(score) }}
                                />
                            ))}
                        </div>
                        {/* Show score */}
                        <div className="tile-score" style={{ color: getScoreColor(score) }}>
                            {score}
                        </div>
                    </div>
                );
            }
        }
        return null;
    };

    // CUSTOM TILE STYLING
    const getTileClassName = ({ date, view }) => {
        if (view === 'month') {
            const dateStr = date.toISOString().split('T')[0];
            if (entriesMap[dateStr]) {
                return 'has-entry';  // Add CSS class
            }
        }
        return '';
    };

    // HANDLE DAY CLICK
    const handleDayClick = (value) => {
        const dateStr = value.toISOString().split('T')[0];
        const entry = entriesMap[dateStr];

        if (entry) {
            setSelectedEntry(entry);  // Show in sidebar
        } else {
            setSelectedEntry(null);  // Clear sidebar
        }
        setDate(value);
    };

    const getScoreColor = (score) => {
        if (score <= 3) return '#9BA8B8';
        if (score <= 7) return '#B8C9D9';
        return '#7EC4CF';
    };

    return (
        <div className="calendar-page-container">
            {/* LEFT SIDE:  Calendar */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="calendar-container card"
            >
                <h2 className="calendar-title">Emotional Journey Calendar</h2>
                <p className="calendar-subtitle">Click on any day to view your emotions and score</p>

                {/* REACT-CALENDAR COMPONENT */}
                <Calendar
                    onChange={handleDayClick}
                    value={date}
                    tileContent={getTileContent}        // Custom content on tiles
                    tileClassName={getTileClassName}    // Custom CSS classes
                    onActiveStartDateChange={({ activeStartDate }) => fetchMonthEntries(activeStartDate)}  // Month changed
                />

                {/* LEGEND */}
                <div className="calendar-legend">
                    <div className="legend-item">
                        <div className="legend-dot" style={{ background: '#7EC4CF' }} />
                        <span>Positive (8-10)</span>
                    </div>
                    <div className="legend-item">
                        <div className="legend-dot" style={{ background: '#B8C9D9' }} />
                        <span>Neutral (4-7)</span>
                    </div>
                    <div className="legend-item">
                        <div className="legend-dot" style={{ background: '#9BA8B8' }} />
                        <span>Challenging (1-3)</span>
                    </div>
                </div>
            </motion.div>

            {/* RIGHT SIDE:  Selected Entry Details */}
            {selectedEntry ? (
                <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="selected-entry card"
                >
                    <h3>
                        {new Date(selectedEntry.date).toLocaleDateString('en-US', {
                            weekday: 'long',
                            month: 'long',
                            day: 'numeric',
                            year: 'numeric'
                        })}
                    </h3>

                    <div className="entry-score-display">
                        <div
                            className="score-badge"
                            style={{ background: getScoreColor(selectedEntry.analysis.emotion_score) }}
                        >
                            {selectedEntry.analysis.emotion_score}
                        </div>
                        <span>Emotional Intensity</span>
                    </div>

                    <div className="entry-emotions-list">
                        <h4>Top Emotions: </h4>
                        {selectedEntry.analysis.top_emotions.map((emotion, index) => (
                            <div key={index} className="entry-emotion-item">
                                <span className="emotion-number">#{index + 1}</span>
                                <span className="emotion-text">{emotion.emotion}</span>
                                <span className="emotion-prob">
                                    {(emotion.probability * 100).toFixed(1)}%
                                </span>
                            </div>
                        ))}
                    </div>

                    <div className="entry-preview">
                        <h4>Diary Preview:</h4>
                        <p>{selectedEntry.content.substring(0, 200)}...</p>
                    </div>
                </motion.div>
            ) : (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="empty-selection card"
                >
                    <div className="empty-icon">📅</div>
                    <p>Select a day with an entry to view details</p>
                </motion.div>
            )}
        </div>
    );
};

export default EmotionCalendar;