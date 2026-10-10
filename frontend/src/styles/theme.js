export const theme = {
    colors: {
        // Primary colors - your main brand colors (ocean blues)
        primary: '#6B9DC9',        // Main button color, links
        primaryLight: '#A8C9E8',   // Hover states, lighter backgrounds
        primaryDark: '#4A7BA7',    // Active states, emphasis

        // Secondary colors - supporting colors
        secondary: '#89B5D9',
        accent: '#B8D4E8',         // For highlights and special elements

        // Background colors - what sits behind your content
        background: '#F5F9FC',     // Page background (very subtle blue-white)
        surface: '#FFFFFF',        // Card/container backgrounds
        surfaceHover: '#EBF4FA',   // When hovering over cards

        // Text colors - different weights for visual hierarchy
        text: {
            primary: '#2C3E50',      // Main text (headings, important info)
            secondary: '#5A6C7D',    // Secondary text (descriptions)
            light: '#8499AA',        // Subtle text (timestamps, hints)
        },

        // Emotion-specific colors - visual feedback for moods
        emotions: {
            positive: '#7EC4CF',     // Happy, excited (score 8-10)
            neutral: '#B8C9D9',      // Calm, content (score 4-7)
            negative: '#9BA8B8',     // Sad, anxious (score 1-3)
        },

        border: '#D4E4F0',         // Lines between elements
        shadow: 'rgba(107, 157, 201, 0.1)', // Soft shadows for depth
    },

    // Spacing system - consistent gaps between elements
    // Using a system prevents random spacing that looks messy
    spacing: {
        xs: '0.25rem',   // 4px
        sm: '0.5rem',    // 8px
        md: '1rem',      // 16px (most common)
        lg: '1.5rem',    // 24px
        xl: '2rem',      // 32px
        xxl: '3rem',     // 48px
    },

    // Border radius - how rounded corners are
    borderRadius: {
        sm: '8px',       // Slightly rounded
        md: '12px',      // Medium rounded (most common)
        lg: '16px',      // Very rounded
        full: '9999px',  // Perfect circle
    },

    // Shadows - create depth and layering
    // Bigger shadows = element appears "higher" above the page
    shadows: {
        sm: '0 2px 8px rgba(107, 157, 201, 0.08)',   // Subtle
        md: '0 4px 16px rgba(107, 157, 201, 0.12)',  // Normal
        lg: '0 8px 24px rgba(107, 157, 201, 0.16)',  // Dramatic
    },

    // Transitions - how fast things animate
    transitions: {
        default: 'all 0.3s ease',  // 0.3 seconds feels natural
        fast: 'all 0.15s ease',    // Quick feedback
    },

    // Fonts - typography system
    fonts: {
        primary: "'Inter', sans-serif",    // Body text - readable
        heading: "'Poppins', sans-serif",  // Headings - distinctive
    },
};