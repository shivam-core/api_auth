import { useState } from 'react';
import { api } from '../api/client';

export function SecurityLab() {
    const [running, setRunning] = useState<string | null>(null);
    const [results, setResults] = useState<Record<string, any>>({});

    const runExperiment = async (name: string, endpoint: string) => {
        setRunning(name);
        try {
            const result = await api<any>(endpoint, { method: 'POST' });
            setResults(prev => ({ ...prev, [name]: result }));
        } catch (e: any) {
            setResults(prev => ({ ...prev, [name]: { error: e.message } }));
        } finally {
            setRunning(null);
        }
    };

    return (
        <div>
            <h1>Security Lab</h1>
            <p style={{ color: 'var(--text-secondary)' }}>
                Run interactive cryptography experiments directly against the CipherGate backend.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 24, marginTop: 32 }}>
                {/* Bruteforce Experiment */}
                <div style={{ padding: 24, border: '1px solid var(--border)', borderRadius: 8, background: 'var(--surface)' }}>
                    <h2>Argon2id Memory Hardness</h2>
                    <p>Evaluates the Argon2id parameters by executing hashing loops to measure offline bruteforce resistance.</p>
                    <button 
                        onClick={() => runExperiment('bruteforce', '/api/experiments/bruteforce')}
                        disabled={running === 'bruteforce'}
                        style={{ padding: '8px 16px', background: 'var(--primary)', color: 'white', border: 'none', borderRadius: 4, cursor: running === 'bruteforce' ? 'wait' : 'pointer' }}
                    >
                        {running === 'bruteforce' ? 'Running...' : 'Run Bruteforce Test'}
                    </button>
                    {results['bruteforce'] && (
                        <div style={{ marginTop: 16, padding: 16, background: '#1e1e1e', color: '#d4d4d4', borderRadius: 4 }}>
                            <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                                {JSON.stringify(results['bruteforce'], null, 2)}
                            </pre>
                        </div>
                    )}
                </div>

                {/* Timing Experiment */}
                <div style={{ padding: 24, border: '1px solid var(--border)', borderRadius: 8, background: 'var(--surface)' }}>
                    <h2>Constant-Time Comparisons</h2>
                    <p>Verifies that valid and invalid JWT signature comparisons complete in mathematically indistinguishable time.</p>
                    <button 
                        onClick={() => runExperiment('timing', '/api/experiments/timing')}
                        disabled={running === 'timing'}
                        style={{ padding: '8px 16px', background: 'var(--primary)', color: 'white', border: 'none', borderRadius: 4, cursor: running === 'timing' ? 'wait' : 'pointer' }}
                    >
                        {running === 'timing' ? 'Running...' : 'Run Timing Test'}
                    </button>
                    {results['timing'] && (
                        <div style={{ marginTop: 16, padding: 16, background: '#1e1e1e', color: '#d4d4d4', borderRadius: 4 }}>
                            <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                                {JSON.stringify(results['timing'], null, 2)}
                            </pre>
                        </div>
                    )}
                </div>

                {/* Fuzz Experiment */}
                <div style={{ padding: 24, border: '1px solid var(--border)', borderRadius: 8, background: 'var(--surface)' }}>
                    <h2>AES-GCM Authenticated Fuzzing</h2>
                    <p>Bombards the decryption function with malformed bytes (altered ciphertext, tampered AAD, invalid nonces) to ensure safe rejection via InvalidTag.</p>
                    <button 
                        onClick={() => runExperiment('fuzz', '/api/experiments/fuzz')}
                        disabled={running === 'fuzz'}
                        style={{ padding: '8px 16px', background: 'var(--primary)', color: 'white', border: 'none', borderRadius: 4, cursor: running === 'fuzz' ? 'wait' : 'pointer' }}
                    >
                        {running === 'fuzz' ? 'Running...' : 'Run Fuzz Test'}
                    </button>
                    {results['fuzz'] && (
                        <div style={{ marginTop: 16, padding: 16, background: '#1e1e1e', color: '#d4d4d4', borderRadius: 4 }}>
                            <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                                {JSON.stringify(results['fuzz'], null, 2)}
                            </pre>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
