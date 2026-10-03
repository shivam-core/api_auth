import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './auth/AuthContext';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { Layout } from './components/Layout';
import { Overview } from './pages/Overview';
import { Notes } from './pages/Notes';
import { Documents } from './pages/Documents';
import { SecurityLab } from './pages/SecurityLab';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
    const { user } = useAuth();
    if (!user) return <Navigate to="/login" />;
    return <>{children}</>;
}

export function App() {
    return (
        <AuthProvider>
            <HashRouter>
                <Routes>
                    <Route path="/login" element={<Login />} />
                    <Route path="/register" element={<Register />} />
                    <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
                        <Route index element={<Overview />} />
                        <Route path="notes" element={<Notes />} />
                        <Route path="documents" element={<Documents />} />
                        <Route path="security-lab" element={<SecurityLab />} />
                    </Route>
                </Routes>
            </HashRouter>
        </AuthProvider>
    );
}
