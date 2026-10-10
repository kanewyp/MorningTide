import React, { createContext, useState, useContext, useEffect } from 'react';

// 1. CREATE CONTEXT - like creating a "radio station"
const AuthContext = createContext(null);

// 2. PROVIDER COMPONENT - broadcasts the signal to all children
export const AuthProvider = ({ children }) => {
    // STATE - data that can change (reactive)
    const [user, setUser] = useState(null);        // null = not logged in
    const [loading, setLoading] = useState(true);  // Show loading spinner? 

    // useEffect - runs when component mounts (appears on screen)
    useEffect(() => {
        // Check if user was previously logged in (page refresh)
        const token = localStorage.getItem('token');
        const username = localStorage.getItem('username');

        if (token && username) {
            setUser({ username, token });  // Restore user session
        }
        setLoading(false);  // Done checking
    }, []);  // Empty array = run once on mount

    // Login function - called when user logs in
    const login = (username, token) => {
        localStorage.setItem('token', token);        // Save to browser
        localStorage.setItem('username', username);
        setUser({ username, token });                // Update state
    };

    // Logout function - called when user logs out
    const logout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('username');
        setUser(null);  // Clear state
    };

    // PROVIDE - make these values available to all child components
    return (
        <AuthContext.Provider value={{ user, login, logout, loading }}>
            {children}
        </AuthContext.Provider>
    );
};

// 3. CUSTOM HOOK - easy way to "tune into the radio station"
export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within AuthProvider');
    }
    return context;
};