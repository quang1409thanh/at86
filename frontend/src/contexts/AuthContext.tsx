import React, { createContext, useContext, useEffect, useState } from 'react';

interface AuthContextType {
    user: any; // user type placeholder
    sidebarOpen: boolean;
    toggleSidebar: () => void;
    darkMode: boolean;
    toggleTheme: () => void;
}

const AuthContext = createContext<AuthContextType>({} as AuthContextType);

export function AuthProvider({ children }: { children: React.ReactNode }) {
    // Sidebar State
    const [sidebarOpen, setSidebarOpen] = useState(() => {
        const saved = localStorage.getItem('sidebarOpen');
        return saved !== null ? JSON.parse(saved) : true;
    });

    // Theme State
    const [darkMode, setDarkMode] = useState(() => {
        const saved = localStorage.getItem('darkMode');
        if (saved !== null) return JSON.parse(saved);
        return window.matchMedia('(prefers-color-scheme: dark)').matches;
    });

    // Persist Sidebar
    useEffect(() => {
        localStorage.setItem('sidebarOpen', JSON.stringify(sidebarOpen));
    }, [sidebarOpen]);

    // Apply Theme
    useEffect(() => {
        localStorage.setItem('darkMode', JSON.stringify(darkMode));
        if (darkMode) {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
    }, [darkMode]);

    const toggleSidebar = () => setSidebarOpen(!sidebarOpen);
    const toggleTheme = () => setDarkMode(!darkMode);

    return (
        <AuthContext.Provider value={{
            user: { username: 'Admin User', role: 'admin' },
            sidebarOpen,
            toggleSidebar,
            darkMode,
            toggleTheme
        }}>
            {children}
        </AuthContext.Provider>
    );
}

export const useAuth = () => useContext(AuthContext);

export function ProtectedRoute({ children, adminOnly }: { children: React.ReactNode, adminOnly?: boolean }) {
    const { user } = useAuth();
    // Placeholder auth check
    if (!user) return null; 
    return <>{children}</>;
}
