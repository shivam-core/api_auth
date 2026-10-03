import { useState, useEffect } from 'react';
import { api } from '../api/client';

export function Overview() {
    const [overview, setOverview] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        api<any>('/api/overview')
            .then(setOverview)
            .catch(e => setError(e.message));
    }, []);

    if (error) return <div style={{ color: 'red' }}>Error: {error}</div>;
    if (!overview) return <div>Loading overview...</div>;

    return (
        <div>
            <h1>Overview</h1>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, marginBottom: 32 }}>
                <div style={{ padding: 24, border: '1px solid var(--border)', borderRadius: 8, background: 'var(--surface)' }}>
                    <div style={{ fontSize: '2em', fontWeight: 'bold' }}>{overview.note_count}</div>
                    <div style={{ color: 'var(--text-secondary)' }}>Notes</div>
                </div>
                <div style={{ padding: 24, border: '1px solid var(--border)', borderRadius: 8, background: 'var(--surface)' }}>
                    <div style={{ fontSize: '2em', fontWeight: 'bold' }}>{overview.document_count}</div>
                    <div style={{ color: 'var(--text-secondary)' }}>Documents</div>
                </div>
                <div style={{ padding: 24, border: '1px solid var(--border)', borderRadius: 8, background: 'var(--surface)' }}>
                    <div style={{ fontSize: '2em', fontWeight: 'bold' }}>{(overview.storage_used_bytes / 1024).toFixed(2)}</div>
                    <div style={{ color: 'var(--text-secondary)' }}>Storage (KB)</div>
                </div>
                <div style={{ padding: 24, border: '1px solid var(--border)', borderRadius: 8, background: 'var(--surface)' }}>
                    <div style={{ fontSize: '2em', fontWeight: 'bold' }}>{overview.active_sessions}</div>
                    <div style={{ color: 'var(--text-secondary)' }}>Active Sessions</div>
                </div>
            </div>

            <h2>Recent Activity</h2>
            <div style={{ border: '1px solid var(--border)', borderRadius: 8, overflow: 'hidden' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                    <thead style={{ background: 'var(--surface)' }}>
                        <tr>
                            <th style={{ padding: 12, borderBottom: '1px solid var(--border)' }}>Time</th>
                            <th style={{ padding: 12, borderBottom: '1px solid var(--border)' }}>Event</th>
                            <th style={{ padding: 12, borderBottom: '1px solid var(--border)' }}>Outcome</th>
                            <th style={{ padding: 12, borderBottom: '1px solid var(--border)' }}>Source</th>
                        </tr>
                    </thead>
                    <tbody>
                        {overview.recent_events.map((ev: any) => (
                            <tr key={ev.id}>
                                <td style={{ padding: 12, borderBottom: '1px solid var(--border)' }}>
                                    {new Date(ev.created_at * 1000).toLocaleString()}
                                </td>
                                <td style={{ padding: 12, borderBottom: '1px solid var(--border)' }}>{ev.event}</td>
                                <td style={{ padding: 12, borderBottom: '1px solid var(--border)' }}>
                                    <span style={{ color: ev.outcome === 'SUCCESS' ? 'green' : 'red' }}>
                                        {ev.outcome}
                                    </span>
                                </td>
                                <td style={{ padding: 12, borderBottom: '1px solid var(--border)' }}>{ev.source}</td>
                            </tr>
                        ))}
                        {overview.recent_events.length === 0 && (
                            <tr>
                                <td colSpan={4} style={{ padding: 12, textAlign: 'center', color: 'var(--text-secondary)' }}>No recent activity.</td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
