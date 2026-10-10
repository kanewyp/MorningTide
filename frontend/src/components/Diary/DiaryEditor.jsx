import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Send, Loader } from 'lucide-react';
import { journalAPI } from '../../services/api';
import EmotionResult from './EmotionResult';
import './Diary.css';

const DiaryEditor = () => {
    // MULTIPLE STATE VARIABLES - each has a specific purpose
    const [content, setContent] = useState('');        // Diary text
    const [loading, setLoading] = useState(false);     // Show spinner?  
    const [analysis, setAnalysis] = useState(null);    // ML results (null = not analyzed)
    const [entryId, setEntryId] = useState(null);      // Database ID (null = not saved)

    // SAVE DIARY ENTRY
    const handleSave = async () => {
        // Guard clause - prevent empty saves
        if (!content.trim()) return;

        setLoading(true);
        try {
            const today = new Date().toISOString().split('T')[0];  // Format: "2026-01-12"
            console.log('🔄 Saving entry with content:', content.substring(0, 50) + '...');

            const response = await journalAPI.createEntry(content, today);

            console.log('✅ Save response:', response.data);
            console.log('📝 Entry ID received:', response.data.id);

            setEntryId(response.data.id);  // Store ID for analysis
            setContent('');  // Clear textarea
            setAnalysis(null);  // Clear any previous analysis

            alert('Diary entry saved successfully!');

        } catch (error) {
            console.error('❌ Save error:', error);
            alert('Failed to save entry:   ' + (error.response?.data?.message || error.message));
        } finally {
            setLoading(false);
        }
    };

    // ANALYZE WITH ML MODELS
    const handleAnalyze = async () => {
        console.log('🔍 Analyze clicked.  entryId:', entryId);

        // Can't analyze if not saved yet
        if (!entryId) {
            console.warn('⚠️ No entryId - user must save first');
            alert('Please save your diary entry first! ');
            return;
        }

        setLoading(true);
        setAnalysis(null);  // Clear old analysis

        try {
            // Step 1: Trigger analysis (calls your DistilBERT model)
            console.log('📊 Step 1: Triggering analysis for entry', entryId);
            const analyzeResponse = await journalAPI.analyzeEntry(entryId);
            console.log('✅ Analysis triggered.  Response:', analyzeResponse.data);

            // Step 2: Fetch results
            console.log('📊 Step 2: Fetching analysis results');
            const analysisResponse = await journalAPI.getAnalysis(entryId);
            console.log('✅ Analysis results retrieved:', analysisResponse.data);

            setAnalysis(analysisResponse.data);

            // Now EmotionResult component will show! 

        } catch (error) {
            console.error('❌ Analyze error:', error);
            console.error('Error response:', error.response);
            console.error('Error message:', error.message);
            alert('Failed to analyze entry: ' + (error.response?.data?.message || error.message));
        } finally {
            setLoading(false);
        }
    };

    // RESET FOR NEW ENTRY
    const handleNewEntry = () => {
        setContent('');
        setAnalysis(null);
        setEntryId(null);
    };

    return (
        <div className="diary-editor-container">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="diary-editor card"
            >
                {/* HEADER WITH DATE */}
                <div className="editor-header">
                    <h2>Today's Diary</h2>
                    <p className="date-display">
                        {new Date().toLocaleDateString('en-US', {
                            weekday: 'long',      // "Monday"
                            year: 'numeric',      // "2026"
                            month: 'long',        // "January"
                            day: 'numeric'        // "12"
                        })}
                    </p>
                    {entryId && (
                        <p style={{ fontSize: '0.85rem', color: '#999' }}>
                            Entry ID: {entryId} ✓
                        </p>
                    )}
                </div>

                {/* TEXTAREA - where user writes */}
                <textarea
                    className="diary-textarea"
                    placeholder="How are you feeling today?  Write about your day, your thoughts, your emotions..."
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    disabled={loading}  // Disable while loading
                />

                {/* ACTION BUTTONS */}
                <div className="editor-actions">
                    <button
                        className="btn btn-secondary"
                        onClick={handleNewEntry}
                        disabled={loading}
                    >
                        New Entry
                    </button>

                    <div className="action-buttons">
                        {/* SAVE BUTTON */}
                        <button
                            className="btn btn-primary"
                            onClick={handleSave}
                            disabled={loading || !content.trim()}  // Disable if loading OR empty
                        >
                            {loading ? <Loader className="spin" size={20} /> : <Send size={20} />}
                            Save Entry
                        </button>

                        {/* ANALYZE BUTTON */}
                        <button
                            className="btn btn-primary"
                            onClick={handleAnalyze}
                            disabled={loading || !entryId}  // Disable if loading OR not saved
                            title={!entryId ? "Save entry first" : "Analyze with ML"}
                        >
                            {loading ? <Loader className="spin" size={20} /> : '🔍'}
                            Analyze
                        </button>
                    </div>
                </div>
            </motion.div>

            {/* CONDITIONAL RENDERING:  Only show if analysis exists */}
            {analysis && (
                <EmotionResult analysis={analysis} />
            )}
        </div>
    );
};

export default DiaryEditor;