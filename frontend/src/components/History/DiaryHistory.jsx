import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Calendar as CalendarIcon, Trash2 as TrashIcon } from 'lucide-react';
import { journalAPI, deleteEntry } from '../../services/api'; // Import deleteEntry
import './DiaryHistory.css';

const DiaryHistory = () => {
    const [entries, setEntries] = useState([]);
    const [selectedEntry, setSelectedEntry] = useState(null);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState(''); // For filtering
    const [deleting, setDeleting] = useState(false); // For delete button feedback

    // FETCH ALL ENTRIES ON MOUNT
    useEffect(() => {
        fetchAllEntries();
    }, []);

    const fetchAllEntries = async () => {
        setLoading(true);
        try {
            const endDate = new Date().toISOString().split('T')[0];
            const startDate = new Date();
            startDate.setMonth(startDate.getMonth() - 6); // Go back 6 months
            const startDateStr = startDate.toISOString().split('T')[0];

            const response = await journalAPI.getEntries(startDateStr, endDate);
            setEntries(response.data.reverse());

            if (response.data.length > 0) {
                setSelectedEntry(response.data[0]);
            }
        } catch (error) {
            console.error('Failed to fetch entries:', error);
        } finally {
            setLoading(false);
        }
    };

    // DELETE ENTRY FUNCTION
    const handleDeleteEntry = async () => {
        if (!selectedEntry) return;

        const confirmDelete = window.confirm(
            `Are you sure you want to delete this entry? This action cannot be undone.`
        );

        if (!confirmDelete) return;

        setDeleting(true); // Show loading state for delete button

        try {
            // Call the API to delete the entry
            await deleteEntry(selectedEntry.id);

            // Update the entries list by filtering out the deleted entry
            setEntries((prevEntries) =>
                prevEntries.filter((entry) => entry.id !== selectedEntry.id)
            );

            // Clear the selected entry
            setSelectedEntry(null);

            alert('Entry deleted successfully!');
        } catch (error) {
            console.error('Failed to delete entry:', error);
            alert('Failed to delete the entry. Please try again.');
        } finally {
            setDeleting(false); // Reset delete button state
        }
    };

    // Filtered entries for search functionality
    const filteredEntries = entries.filter(
        (entry) =>
            entry.content.toLowerCase().includes(searchTerm.toLowerCase()) ||
            entry.date.includes(searchTerm)
    );

    const getScoreColor = (score) => {
        if (score <= 3) return '#9BA8B8';
        if (score <= 7) return '#B8C9D9';
        return '#7EC4CF';
    };

    return (
        <div className="history-container">
            {/* LEFT SIDEBAR - Entry List */}
            <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className="history-sidebar card"
            >
                <div className="sidebar-header">
                    <h2>Diary Entries</h2>
                    <div className="search-box">
                        <Search size={18} />
                        <input
                            type="text"
                            placeholder="Search entries..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="search-input"
                        />
                    </div>
                </div>

                <div className="entries-list">
                    {loading ? (
                        <div className="loading-state">Loading entries...</div>
                    ) : filteredEntries.length === 0 ? (
                        <div className="empty-state">
                            <p>No entries found</p>
                        </div>
                    ) : (
                        filteredEntries.map((entry) => (
                            <motion.div
                                key={entry.id}
                                whileHover={{ scale: 1.02 }}
                                onClick={() => setSelectedEntry(entry)}
                                className={`entry-item ${selectedEntry?.id === entry.id ? 'selected' : ''
                                    }`}
                            >
                                <div className="entry-item-header">
                                    <CalendarIcon size={16} />
                                    <span className="entry-date">
                                        {new Date(entry.date).toLocaleDateString('en-US', {
                                            month: 'short',
                                            day: 'numeric',
                                            year: 'numeric',
                                        })}
                                    </span>
                                </div>
                                <p className="entry-preview">{entry.content.substring(0, 80)}...</p>
                                {entry.analysis && (
                                    <div className="entry-score-badge">
                                        <span
                                            className="score-dot"
                                            style={{
                                                background: getScoreColor(entry.analysis.emotion_score),
                                            }}
                                        />
                                        <span>Score: {entry.analysis.emotion_score}</span>
                                    </div>
                                )}
                            </motion.div>
                        ))
                    )}
                </div>
            </motion.div>

            {/* RIGHT PANEL - Entry Details */}
            <div className="history-detail">
                <AnimatePresence mode="wait">
                    {selectedEntry ? (
                        <motion.div
                            key={selectedEntry.id}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            className="detail-content card"
                        >
                            <div className="detail-header">
                                <h2>
                                    {new Date(selectedEntry.date).toLocaleDateString('en-US', {
                                        weekday: 'long',
                                        month: 'long',
                                        day: 'numeric',
                                        year: 'numeric',
                                    })}
                                </h2>
                                <span className="detail-time">
                                    Written on{' '}
                                    {new Date(selectedEntry.created_at).toLocaleString()}
                                </span>
                            </div>

                            <div className="detail-body">
                                <div className="diary-content">
                                    <h3>Diary Entry</h3>
                                    <p>{selectedEntry.content}</p>
                                </div>

                                {selectedEntry.analysis ? (
                                    <div className="detail-analysis">
                                        <h3>Emotional Analysis</h3>
                                        <div className="analysis-score">
                                            <div
                                                className="score-circle-large"
                                                style={{
                                                    background: getScoreColor(selectedEntry.analysis.emotion_score),
                                                }}
                                            >
                                                {selectedEntry.analysis.emotion_score}
                                            </div>
                                            <div className="score-info">
                                                <span className="score-label">Emotional Intensity</span>
                                                <span className="score-description">
                                                    {selectedEntry.analysis.emotion_score <= 3
                                                        ? 'A challenging day'
                                                        : selectedEntry.analysis.emotion_score <= 7
                                                            ? 'A balanced day'
                                                            : 'A positive day'}
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="no-analysis">
                                        <p>This entry hasn't been analyzed yet. </p>
                                        <p className="hint">Go to the Diary page to analyze it!</p>
                                    </div>
                                )}
                            </div>

                            {/* DELETE BUTTON */}
                            <button
                                className="btn-delete"
                                onClick={handleDeleteEntry}
                                disabled={deleting}
                            >
                                <TrashIcon size={16} />
                                {deleting ? 'Deleting...' : 'Delete Entry'}
                            </button>
                        </motion.div>
                    ) : (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="detail-empty card"
                        >
                            <div className="empty-icon">📖</div>
                            <h3>No Entry Selected</h3>
                            <p>Select an entry from the list to view details</p>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
};

export default DiaryHistory;