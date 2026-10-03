import { useState, useEffect } from 'react';
import { api } from '../api/client';

export function Notes() {
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
        <div style={{ display: 'flex', height: '100%', gap: 32 }}>
            <div style={{ width: 250, display: 'flex', flexDirection: 'column' }}>
                <h2>Notes</h2>
                <ul style={{ listStyle: 'none', padding: 0, flex: 1, overflowY: 'auto' }}>
                    <li 
                        style={{ padding: 12, marginBottom: 8, cursor: 'pointer', borderRadius: 4, background: !selectedNote ? 'var(--primary)' : 'transparent', color: !selectedNote ? 'white' : 'var(--text)' }} 
                        onClick={() => setSelectedNote(null)}
                    >
                        + New Note
                    </li>
                    {notes.map(n => (
                        <li 
                            key={n.id} 
                            style={{ padding: 12, marginBottom: 8, cursor: 'pointer', borderRadius: 4, background: selectedNote?.id === n.id ? 'var(--surface)' : 'transparent', border: '1px solid', borderColor: selectedNote?.id === n.id ? 'var(--border)' : 'transparent' }} 
                            onClick={() => handleSelect(n.id)}
                        >
                            {n.title}
                        </li>
                    ))}
                </ul>
            </div>
            <div style={{ flex: 1 }}>
                {selectedNote ? (
                    <div>
                        <h2>{selectedNote.title}</h2>
                        <div style={{ padding: 24, border: '1px solid var(--border)', borderRadius: 8, background: 'var(--surface)', minHeight: 200, marginBottom: 32 }}>
                            {selectedNote.body}
                        </div>
                        
                        <h3>Encryption Envelope</h3>
                        <div style={{ padding: 16, border: '1px solid var(--border)', background: '#1e1e1e', color: '#d4d4d4', borderRadius: 8, overflowX: 'auto' }}>
                            <pre style={{ margin: 0, fontFamily: 'monospace' }}>
                                {JSON.stringify(selectedNote.envelope, null, 2)}
                            </pre>
                        </div>
                    </div>
                ) : (
                    <div>
                        <h2>Create Note</h2>
                        <form onSubmit={handleCreate}>
                            <div style={{ marginBottom: 16 }}>
                                <label style={{ display: 'block', marginBottom: 8 }}>Title</label>
                                <input type="text" value={title} onChange={e => setTitle(e.target.value)} required style={{ width: '100%', padding: 8, borderRadius: 4, border: '1px solid var(--border)' }} />
                            </div>
                            <div style={{ marginBottom: 16 }}>
                                <label style={{ display: 'block', marginBottom: 8 }}>Body</label>
                                <textarea value={body} onChange={e => setBody(e.target.value)} rows={10} required style={{ width: '100%', padding: 8, borderRadius: 4, border: '1px solid var(--border)' }} />
                            </div>
                            <button type="submit" style={{ padding: '8px 16px', background: 'var(--primary)', color: 'white', border: 'none', borderRadius: 4, cursor: 'pointer' }}>
                                Save Note
                            </button>
                        </form>
                    </div>
                )}
            </div>
        </div>
    );
}
