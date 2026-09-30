import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { api } from '../api/client';

export function Register() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        try {
            await api('/api/auth/register', {
                method: 'POST',
                body: JSON.stringify({ username, password })
            });
            navigate('/login');
        } catch (err: any) {
            setError(err.message || 'Registration failed');
        }
    };

    return (
        <div style={{ maxWidth: 400, margin: '40px auto' }}>
            <h1>Register</h1>
            {error && <div style={{ color: 'red' }}>{error}</div>}
            <form onSubmit={handleSubmit}>
                <div>
                    <label>Username</label><br />
                    <input type="text" value={username} onChange={e => setUsername(e.target.value)} pattern="^[a-z0-9_]{3,32}$" required />
                </div>
                <div>
                    <label>Password</label><br />
                    <input type="password" value={password} onChange={e => setPassword(e.target.value)} minLength={12} required />
                </div>
                <button type="submit">Register</button>
            </form>
            <p><Link to="/login">Login here</Link></p>
        </div>
    );
}
