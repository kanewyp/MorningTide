import axios from "axios";

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        "Content-Type": "application/json",
    },
});

// INTERCEPTOR - attach token correctly
api.interceptors.request.use((config) => {
    const token = localStorage.getItem("token");
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// AUTH API
export const authAPI = {
    signup: (username, password) => api.post("/auth/signup", { username, password }),
    login: (username, password) => api.post("/auth/login", { username, password }),
    logout: () => {
        localStorage.removeItem("token");
        localStorage.removeItem("username");
    },
};

// JOURNAL API
export const journalAPI = {
    createEntry: (content, date) => api.post("/api/journal/entries", { content, date }),
    getEntries: (startDate, endDate) =>
        api.get("/api/journal/entries", { params: { start_date: startDate, end_date: endDate } }),
    getEntry: (entryId) => api.get(`/api/journal/entries/${entryId}`),

    // Analyze endpoint
    analyzeEntry: (entryId) => api.post("/api/analysis/analyze", { entry_id: entryId }),

    // Get analysis results - FIXED PATH
    getAnalysis: (entryId) => api.get(`/api/analysis/${entryId}`),
};

export const ragAPI = {
    generateSuggestions: (payload) => api.post("/api/rag/generate-suggestions", payload),
    retrieveTopics: (query, topK = 5) =>
        api.post("/api/rag/retrieve-topics", { query, top_k: topK }),
    health: () => api.get("/api/rag/health"),
};

export const deleteEntry = async (entryId) => {
    const response = await api.delete(`/api/journal/entries/${entryId}`);
    return response.data;
};

export default api;