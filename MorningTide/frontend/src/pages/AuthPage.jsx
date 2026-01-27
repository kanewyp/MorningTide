import React, { useState } from 'react';
import { motion } from 'framer-motion';
import Login from '../components/Auth/Login';
import Signup from '../components/Auth/Signup';
import './AuthPage.css';

const AuthPage = () => {
    // STATE:  Track which form to show
    const [isLogin, setIsLogin] = useState(true);  // Start with login

    return (
        <div className="auth-page">
            {/* BACKGROUND ANIMATION */}
            <div className="wave-background">
                <div className="wave"></div>
                <div className="wave"></div>
            </div>

            <div className="auth-content">
                {/* LOGO/BRANDING */}
                <motion.div
                    initial={{ scale: 0, rotate: -180 }}
                    animate={{ scale: 1, rotate: 0 }}
                    transition={{
                        type: 'spring',  // Physics-based animation
                        stiffness: 260,  // How "bouncy"
                        damping: 20      // How much it oscillates
                    }}
                    className="auth-logo"
                >
                    <span className="logo-wave">🌊</span>
                    <h1 className="logo-text">MorningTide</h1>
                    <p className="logo-tagline">Navigate your emotions, one wave at a time</p>
                </motion.div>

                {/* CONDITIONAL RENDERING:  Show Login OR Signup */}
                {/* AnimatePresence allows exit animations when component unmounts */}
                <motion.div
                    key={isLogin ? 'login' : 'signup'}  // Key changes trigger re-mount
                    initial={{ opacity: 0, x: isLogin ? -20 : 20 }}  // Slide from sides
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: isLogin ? 20 : -20 }}
                    transition={{ duration: 0.3 }}
                >
                    {isLogin ? (
                        <Login onSwitchToSignup={() => setIsLogin(false)} />
                    ) : (
                        <Signup onSwitchToLogin={() => setIsLogin(true)} />
                    )}
                </motion.div>
            </div>
        </div>
    );
};

export default AuthPage;