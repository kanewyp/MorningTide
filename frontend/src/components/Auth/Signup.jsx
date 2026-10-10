import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { authAPI } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import './Auth.css';

const Signup = ({ onSwitchToLogin }) => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');  // NEW: Confirm password
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        // CLIENT-SIDE VALIDATION - check before sending to server
        // This gives instant feedback (better UX than waiting for server)

        if (password !== confirmPassword) {
            setError('Passwords do not match');
            return;  // Stop execution - don't call API
        }

        if (password.length < 6) {
            setError('Password must be at least 6 characters');
            return;
        }

        setLoading(true);

        try {
            const response = await authAPI.signup(username, password);
            // After successful signup, automatically log them in
            login(username, response.data.token);

        } catch (err) {
            // Server-side validation failed (username taken, etc.)
            setError(err.response?.data?.message || 'Signup failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="auth-container"
        >
            <div className="auth-header">
                <h1 className="auth-title">Begin Your Journey</h1>
                <p className="auth-subtitle">Create an account to start tracking your emotions</p>
            </div>

            <form onSubmit={handleSubmit} className="auth-form">
                {error && (
                    <div className="error-message">
                        {error}
                    </div>
                )}

                <div className="form-group">
                    <label htmlFor="username">Username</label>
                    <input
                        id="username"
                        type="text"
                        className="input"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        placeholder="Choose a username"
                        required
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="password">Password</label>
                    <input
                        id="password"
                        type="password"
                        className="input"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="Create a password"
                        required
                    />
                </div>

                {/* NEW FIELD: Confirm password */}
                <div className="form-group">
                    <label htmlFor="confirmPassword">Confirm Password</label>
                    <input
                        id="confirmPassword"
                        type="password"
                        className="input"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        placeholder="Confirm your password"
                        required
                    />
                </div>

                <button
                    type="submit"
                    className="btn btn-primary auth-submit"
                    disabled={loading}
                >
                    {loading ? 'Creating account...' : 'Sign Up'}
                </button>
            </form>

            <div className="auth-footer">
                <p>
                    Already have an account?{' '}
                    <button className="link-button" onClick={onSwitchToLogin}>
                        Sign in
                    </button>
                </p>
            </div>
        </motion.div>
    );
};

export default Signup;