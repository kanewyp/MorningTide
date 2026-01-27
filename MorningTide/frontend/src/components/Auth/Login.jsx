import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { authAPI } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import './Auth.css';

const Login = ({ onSwitchToSignup }) => {
    // LOCAL STATE - data specific to this component
    const [username, setUsername] = useState('');  // Controlled input
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');        // Error message
    const [loading, setLoading] = useState(false); // Disable button while loading

    // Get login function from context
    const { login } = useAuth();

    // FORM SUBMISSION HANDLER
    const handleSubmit = async (e) => {
        e.preventDefault();  // Prevent page refresh (default form behavior)
        setError('');        // Clear previous errors
        setLoading(true);    // Show loading state

        try {
            // Call API (this is async - takes time)
            const response = await authAPI.login(username, password);

            // Success!  Update global auth state
            login(username, response.data.token);
            // AuthContext will trigger re-render, showing logged-in UI

        } catch (err) {
            // API call failed - show error message
            setError(err.response?.data?.message || 'Login failed.  Please try again.');
        } finally {
            // Always runs (success or failure)
            setLoading(false);
        }
    };

    return (
        // FRAMER MOTION - adds enter animation
        <motion.div
            initial={{ opacity: 0, y: 20 }}  // Start:  invisible, below
            animate={{ opacity: 1, y: 0 }}   // End: visible, in place
            className="auth-container"
        >
            <div className="auth-header">
                <h1 className="auth-title">Welcome Back</h1>
                <p className="auth-subtitle">Sign in to continue your journey</p>
            </div>

            {/* FORM - handles user input */}
            <form onSubmit={handleSubmit} className="auth-form">

                {/* CONDITIONAL RENDERING - only show if error exists */}
                {error && (
                    <div className="error-message">
                        {error}
                    </div>
                )}

                {/* CONTROLLED INPUT - React controls the value */}
                <div className="form-group">
                    <label htmlFor="username">Username</label>
                    <input
                        id="username"
                        type="text"
                        className="input"
                        value={username}  // Value comes from state
                        onChange={(e) => setUsername(e.target.value)}  // Update state on change
                        placeholder="Enter your username"
                        required  // HTML5 validation
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="password">Password</label>
                    <input
                        id="password"
                        type="password"  // Hides the text
                        className="input"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="Enter your password"
                        required
                    />
                </div>

                {/* SUBMIT BUTTON - disabled while loading */}
                <button
                    type="submit"
                    className="btn btn-primary auth-submit"
                    disabled={loading}
                >
                    {loading ? 'Signing in...' : 'Sign In'}  {/* Dynamic text */}
                </button>
            </form>

            {/* SWITCH TO SIGNUP */}
            <div className="auth-footer">
                <p>
                    Don't have an account?{' '}
                    <button className="link-button" onClick={onSwitchToSignup}>
                        Sign up
                    </button>
                </p>
            </div>
        </motion.div>
    );
};

export default Login;