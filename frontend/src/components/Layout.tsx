import { useAuth } from '../auth/AuthContext';
import { NavLink, Outlet } from 'react-router-dom';

export function Layout() {
    const { user, logout } = useAuth();

    return (
        <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
            <div style={{ width: 250, padding: 24, borderRight: '1px solid var(--border)', background: 'var(--surface)', display: 'flex', flexDirection: 'column' }}>
                <h2 style={{ margin: '0 0 8px 0' }}>CipherGate</h2>
                <div style={{ fontSize: '0.9em', color: 'var(--text-secondary)', marginBottom: 32 }}>
                    Welcome, {user?.username}
                </div>

                <nav style={{ display: 'flex', flexDirection: 'column', gap: 12, flex: 1 }}>
                    <NavLink to="/" style={({ isActive }) => ({ textDecoration: 'none', color: isActive ? 'var(--primary)' : 'var(--text)', fontWeight: isActive ? 'bold' : 'normal' })}>
                        Overview
                    </NavLink>
                    <NavLink to="/notes" style={({ isActive }) => ({ textDecoration: 'none', color: isActive ? 'var(--primary)' : 'var(--text)', fontWeight: isActive ? 'bold' : 'normal' })}>
                        Notes
                    </NavLink>
                    <NavLink to="/documents" style={({ isActive }) => ({ textDecoration: 'none', color: isActive ? 'var(--primary)' : 'var(--text)', fontWeight: isActive ? 'bold' : 'normal' })}>
                        Documents
                    </NavLink>
                    <NavLink to="/security-lab" style={({ isActive }) => ({ textDecoration: 'none', color: isActive ? 'var(--primary)' : 'var(--text)', fontWeight: isActive ? 'bold' : 'normal' })}>
                        Security Lab
                    </NavLink>
                </nav>

                <button onClick={logout} style={{ marginTop: 'auto', padding: '8px 16px', border: '1px solid var(--border)', background: 'transparent', cursor: 'pointer', borderRadius: 4 }}>
                    Logout
                </button>
            </div>
            <div style={{ flex: 1, padding: 32, overflowY: 'auto' }}>
                <Outlet />
            </div>
        </div>
    );
}
