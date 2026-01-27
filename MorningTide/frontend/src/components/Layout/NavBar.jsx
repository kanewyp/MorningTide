import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { BookOpen, Calendar, Database, MessageCircle, Volume2, VolumeX, LogOut } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import './NavBar.css';

const NavBar = ({ audioPlaying, toggleAudio }) => {
    // useLocation - tells us which page we're on (from React Router)
    const location = useLocation();
    const { user, logout } = useAuth();

    // NAVIGATION ITEMS - array makes it easy to map over
    const navItems = [
        { path: '/chatbot', icon: MessageCircle, label: 'Chat' },
        { path: '/diary', icon: BookOpen, label: 'Diary' },
        { path: '/calendar', icon: Calendar, label: 'Calendar' },
        { path: '/history', icon: Database, label: 'History' },
    ];

    return (
        <nav className="navbar glass">
            <div className="navbar-container">

                {/* BRAND/LOGO */}
                <Link to="/chatbot" className="navbar-brand">
                    <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{
                            type: 'spring',
                            stiffness: 260,
                            damping: 20
                        }}
                        className="brand-icon"
                    >
                        🌊
                    </motion.div>
                    <span className="brand-text">MorningTide</span>
                </Link>

                {/* NAVIGATION MENU - map over array to create links */}
                <div className="navbar-menu">
                    {navItems.map((item) => {
                        const Icon = item.icon;  // Lucide icon component
                        const isActive = location.pathname === item.path;  // Highlight current page

                        return (
                            <Link
                                key={item.path}  // Unique key for React's reconciliation
                                to={item.path}
                                className={`nav-item ${isActive ? 'active' : ''}`}  // Conditional class
                            >
                                <Icon size={20} />
                                <span>{item.label}</span>
                            </Link>
                        );
                    })}
                </div>

                {/* RIGHT SIDE ACTIONS */}
                <div className="navbar-actions">
                    {/* AUDIO TOGGLE BUTTON */}
                    <button
                        className="icon-button"
                        onClick={toggleAudio}
                        title={audioPlaying ? 'Mute' : 'Play ambient sound'}
                    >
                        {audioPlaying ? <Volume2 size={20} /> : <VolumeX size={20} />}
                    </button>

                    {/* USER MENU */}
                    <div className="user-menu">
                        <span className="username">{user?.username}</span>
                        <button
                            className="icon-button"
                            onClick={logout}
                            title="Logout"
                        >
                            <LogOut size={20} />
                        </button>
                    </div>
                </div>
            </div>
        </nav>
    );
};

export default NavBar;