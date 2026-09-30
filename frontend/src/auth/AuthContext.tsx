import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { api, setAccessToken } from '../api/client';

type User = { id: string; username: string };

type AuthContextType = {
    user: User | null;
    login: (token: string, user: User) => void;
    logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);

    useEffect(() => {
        const handleAuthExpired = () => {
            setUser(null);
            setAccessToken(null);
        };
        window.addEventListener('auth-expired', handleAuthExpired);
        return () => window.removeEventListener('auth-expired', handleAuthExpired);
    }, []);

    const login = (token: string, user: User) => {
        setAccessToken(token);
        setUser(user);
    };

    const logout = async () => {
        try {
            await api('/api/auth/logout', { method: 'POST' });
        } catch (e) {
            console.error(e);
        } finally {
            setUser(null);
            setAccessToken(null);
        }
    };

    return (
        <AuthContext.Provider value={{ user, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
}

export const useAuth = () => {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error("useAuth must be used within AuthProvider");
    return ctx;
};
