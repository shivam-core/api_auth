import { useState, useEffect } from 'react';
import { useAuth } from '../auth/AuthContext';
import { api } from '../api/client';

export function Dashboard() {
    const { user, logout } = useAuth();
    const [notes, setNotes] = useState<any[]>([]);
    const [title, setTitle] = useState('');
    const [body, setBody] = useState('');
    const [selectedNote, setSelectedNote] = useState<any>(null);

    const loadNotes = async () => {
        try {
            const data = await api<any>('/api/notes');
            setNotes(data.items);
        } catch (e) {
            console.error(e);
        }
    };

    useEffect(() => {
        loadNotes();
    }, []);

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await api('/api/notes', {
                method: 'POST',
                body: JSON.stringify({ title, body })
            });
            setTitle('');
            setBody('');
            loadNotes();
        } catch (e) {
            console.error(e);
        }
    };

    const handleSelect = async (id: string) => {
        try {
            const note = await api<any>(`/api/notes/${id}`);
            const envelope = await api<any>(`/api/notes/${id}/envelope`);
            setSelectedNote({ ...note, envelope });
        } catch (e) {
            console.error(e);
        }
    };

    return (
        <div style={{ display: 'flex' }}>
            <div style={{ width: 224, padding: 16, borderRight: '1px solid var(--border)', height: '100vh' }}>
                <h2>CipherGate</h2>
                <p>Welcome, {user?.username}</p>
                <button onClick={logout}>Logout</button>

                <h3 style={{ marginTop: 24 }}>Your Notes</h3>
                <ul style={{ listStyle: 'none', padding: 0 }}>
                    {notes.map(n => (
                        <li key={n.id} style={{ marginBottom: 8, cursor: 'pointer', color: 'var(--accent)' }} onClick={() => handleSelect(n.id)}>
                            {n.title}
                        </li>
                    ))}
                </ul>
            </div>
            <div style={{ flex: 1, padding: 32 }}>
                {selectedNote ? (
                    <div>
                        <button onClick={() => setSelectedNote(null)}>Back to New Note</button>
                        <h2>{selectedNote.title}</h2>
                        <p>{selectedNote.body}</p>
                        
                        <div style={{ marginTop: 32, padding: 16, border: '1px solid var(--border)', background: 'var(--surface)' }}>
                            <h4>Encryption Envelope</h4>
                            <pre style={{ margin: 0, fontFamily: 'monospace' }}>
                                {JSON.stringify(selectedNote.envelope, null, 2)}
                            </pre>
                        </div>
                    </div>
                ) : (
                    <div>
                        <h2>Create Note</h2>
                        <form onSubmit={handleCreate}>
                            <div>
                                <label>Title</label><br />
                                <input type="text" value={title} onChange={e => setTitle(e.target.value)} required />
                            </div>
                            <div style={{ marginTop: 16 }}>
                                <label>Body</label><br />
                                <textarea value={body} onChange={e => setBody(e.target.value)} rows={10} style={{ width: '100%' }} required />
                            </div>
                            <button type="submit" style={{ marginTop: 16 }}>Save Note</button>
                        </form>
                    </div>
                )}
            </div>
        </div>
    );
}
