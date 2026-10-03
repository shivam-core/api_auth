import { useState, useEffect } from 'react';
import { api } from '../api/client';

export function Documents() {
    const [documents, setDocuments] = useState<any[]>([]);
    const [name, setName] = useState('');
    const [content, setContent] = useState('');
    const [selectedDoc, setSelectedDoc] = useState<any>(null);
    const [uploading, setUploading] = useState(false);

    const loadDocuments = async () => {
        try {
            const data = await api<any>('/api/documents');
            setDocuments(data.items);
        } catch (e) {
            console.error(e);
        }
    };

    useEffect(() => {
        loadDocuments();
    }, []);

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        setUploading(true);
        try {
            // content is a string but we need to upload it as a file.
            const blob = new Blob([content], { type: 'text/plain' });
            const formData = new FormData();
            formData.append('file', blob, name || 'document.txt');
            formData.append('display_name', name);
            formData.append('description', 'Uploaded via lab');
            
            await fetch('/api/documents', {
                method: 'POST',
                body: formData,
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            setName('');
            setContent('');
            loadDocuments();
        } catch (e) {
            console.error(e);
        } finally {
            setUploading(false);
        }
    };

    const handleSelect = async (id: string) => {
        try {
            const doc = await api<any>(`/api/documents/${id}`);
            const envelope = await api<any>(`/api/documents/${id}/envelope`);
            
            // fetch content
            const contentRes = await fetch(`/api/documents/${id}/content`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
            });
            const textContent = await contentRes.text();
            
            setSelectedDoc({ ...doc, envelope, textContent });
        } catch (e) {
            console.error(e);
        }
    };

    return (
        <div style={{ display: 'flex', height: '100%', gap: 32 }}>
            <div style={{ width: 250, display: 'flex', flexDirection: 'column' }}>
                <h2>Documents</h2>
                <ul style={{ listStyle: 'none', padding: 0, flex: 1, overflowY: 'auto' }}>
                    <li 
                        style={{ padding: 12, marginBottom: 8, cursor: 'pointer', borderRadius: 4, background: !selectedDoc ? 'var(--primary)' : 'transparent', color: !selectedDoc ? 'white' : 'var(--text)' }} 
                        onClick={() => setSelectedDoc(null)}
                    >
                        + Upload Document
                    </li>
                    {documents.map(d => (
                        <li 
                            key={d.id} 
                            style={{ padding: 12, marginBottom: 8, cursor: 'pointer', borderRadius: 4, background: selectedDoc?.id === d.id ? 'var(--surface)' : 'transparent', border: '1px solid', borderColor: selectedDoc?.id === d.id ? 'var(--border)' : 'transparent' }} 
                            onClick={() => handleSelect(d.id)}
                        >
                            {d.display_name}
                        </li>
                    ))}
                </ul>
            </div>
            
            <div style={{ flex: 1, display: 'flex', gap: 32 }}>
                {selectedDoc ? (
                    <>
                        <div style={{ flex: 1 }}>
                            <h2>{selectedDoc.display_name}</h2>
                            <div style={{ padding: 24, border: '1px solid var(--border)', borderRadius: 8, background: 'var(--surface)', minHeight: 400, whiteSpace: 'pre-wrap' }}>
                                {selectedDoc.textContent}
                            </div>
                        </div>
                        <div style={{ width: 400 }}>
                            <h3>Metadata & Envelopes</h3>
                            <div style={{ padding: 16, border: '1px solid var(--border)', background: '#1e1e1e', color: '#d4d4d4', borderRadius: 8, overflowX: 'auto', maxHeight: 'calc(100vh - 200px)' }}>
                                <pre style={{ margin: 0, fontFamily: 'monospace', fontSize: '0.9em' }}>
                                    {JSON.stringify(selectedDoc.envelope, null, 2)}
                                </pre>
                            </div>
                        </div>
                    </>
                ) : (
                    <div style={{ flex: 1 }}>
                        <h2>Upload Document</h2>
                        <form onSubmit={handleCreate}>
                            <div style={{ marginBottom: 16 }}>
                                <label style={{ display: 'block', marginBottom: 8 }}>Document Name</label>
                                <input type="text" value={name} onChange={e => setName(e.target.value)} required style={{ width: '100%', padding: 8, borderRadius: 4, border: '1px solid var(--border)' }} />
                            </div>
                            <div style={{ marginBottom: 16 }}>
                                <label style={{ display: 'block', marginBottom: 8 }}>Content (Plaintext for simulation)</label>
                                <textarea value={content} onChange={e => setContent(e.target.value)} rows={10} required style={{ width: '100%', padding: 8, borderRadius: 4, border: '1px solid var(--border)' }} />
                            </div>
                            <button type="submit" disabled={uploading} style={{ padding: '8px 16px', background: 'var(--primary)', color: 'white', border: 'none', borderRadius: 4, cursor: uploading ? 'wait' : 'pointer' }}>
                                {uploading ? 'Encrypting...' : 'Encrypt & Upload'}
                            </button>
                        </form>
                    </div>
                )}
            </div>
        </div>
    );
}
