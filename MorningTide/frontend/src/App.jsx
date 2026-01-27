import React, { useState, useEffect, useRef } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import NavBar from './components/Layout/NavBar';
import AuthPage from './pages/AuthPage';
import DiaryPage from './pages/DiaryPage';
import CalendarPage from './pages/CalendarPage';
import HistoryPage from './pages/HistoryPage';
import ChatBotPage from './pages/ChatBotPage';
import './App.css';

// PROTECTED ROUTE COMPONENT - redirects if not logged in
const ProtectedRoute = ({ children }) => {
    const { user, loading } = useAuth();

    // Show nothing while checking auth status
    if (loading) {
        return (
            <div className="loading-screen">
                <div className="spinner">🌊</div>
                <p>Loading MorningTide...</p>
            </div>
        );
    }

    // Redirect to auth page if not logged in
    return user ? children : <Navigate to="/auth" />;
};

// MAIN APP LAYOUT
const AppLayout = () => {
    const [audioPlaying, setAudioPlaying] = useState(false);
    const audioRef = useRef(null);  // Reference to audio element

    // INITIALIZE AUDIO
    useEffect(() => {
        // Create audio element
        audioRef.current = new Audio('/audio/background_music.mp3');  // ← FIXED: Added leading slash
        audioRef.current.loop = true;  // Loop forever
        audioRef.current.volume = 0.3;  // ← FIXED: Changed to 0.3 (matches your comment about 30%)
        audioRef.current.preload = 'auto';  // ← ADDED: Preload the audio

        console.log('🎵 Audio initialized:', audioRef.current.src);  // ← ADDED: Debug log

        // Cleanup when component unmounts
        return () => {
            if (audioRef.current) {
                audioRef.current.pause();
                audioRef.current.src = '';  // ← ADDED: Clear the source
                audioRef.current = null;
            }
        };
    }, []);

    // TOGGLE AUDIO FUNCTION
    const toggleAudio = async () => {  // ← FIXED: Made async
        if (!audioRef.current) {
            console.error('❌ Audio ref is null');
            return;
        }

        try {
            if (audioPlaying) {
                // Pause the audio
                audioRef.current.pause();
                setAudioPlaying(false);
                console.log('⏸️ Audio paused');
            } else {
                // Play the audio
                await audioRef.current.play();  // ← FIXED: Await the promise
                setAudioPlaying(true);
                console.log('▶️ Audio playing');
            }
        } catch (err) {
            console.error('❌ Audio play failed:', err);
            setAudioPlaying(false);  // ← ADDED: Reset state on error
        }
    };

    return (
        <div className="app">
            {/* BACKGROUND WAVES */}
            <div className="wave-background">
                <div className="wave"></div>
                <div className="wave"></div>
            </div>

            {/* NAVIGATION */}
            <NavBar audioPlaying={audioPlaying} toggleAudio={toggleAudio} />

            {/* MAIN CONTENT AREA */}
            <main className="main-content">
                <Routes>
                    {/* Default route - redirect to chatbot */}
                    <Route path="/" element={<Navigate to="/chatbot" />} />

                    {/* Protected routes - require login */}
                    <Route
                        path="/chatbot"
                        element={
                            <ProtectedRoute>
                                <ChatBotPage />
                            </ProtectedRoute>
                        }
                    />
                    <Route
                        path="/diary"
                        element={
                            <ProtectedRoute>
                                <DiaryPage />
                            </ProtectedRoute>
                        }
                    />
                    <Route
                        path="/calendar"
                        element={
                            <ProtectedRoute>
                                <CalendarPage />
                            </ProtectedRoute>
                        }
                    />
                    <Route
                        path="/history"
                        element={
                            <ProtectedRoute>
                                <HistoryPage />
                            </ProtectedRoute>
                        }
                    />
                </Routes>
            </main>
        </div>
    );
};

// ROOT APP COMPONENT
function App() {
    return (
        <Router>
            <AuthProvider>
                <Routes>
                    <Route path="/auth" element={<AuthPage />} />
                    <Route path="/*" element={<AppLayout />} />
                </Routes>
            </AuthProvider>
        </Router>
    );
}

export default App;