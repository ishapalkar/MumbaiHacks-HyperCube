import React, { useState } from 'react';
import './App.css';

function Header() {
  return (
    <header className="tt-header">
      <div className="tt-header-inner">
        <div className="brand">
          <div className="logo">TokenTrust</div>
          <div className="tag">AI-Powered Financial Risk Management</div>
        </div>
        <div className="metrics">
          <div className="metric">68.9%<div className="meta">Accuracy</div></div>
          <div className="metric">&lt;200ms<div className="meta">Response Time</div></div>
          <div className="metric">24/7<div className="meta">Monitoring</div></div>
        </div>
      </div>
    </header>
  );
}

function NavTabs() {
  return (
    <div className="tt-tabs">
      <button className="tab active">🔍 Risk Analysis</button>
      <button className="tab">🔒 Merchant 2FA</button>
      <button className="tab">📈 Live Monitoring</button>
    </div>
  );
}

function App() {
  const [form, setForm] = useState({
    token: '',
    merchant_id: '',
    amount: '',
    token_age_minutes: 30,
    device_trust_score: 0.9,
    usual_location: '',
    current_location: '',
    new_device: false,
    vpn_detected: false,
    unusual_time: false,
    rushed_transaction: false,
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  function update(key, value) {
    setForm(prev => ({ ...prev, [key]: value }));
  }

  async function assignToken() {
    setLoading(true);
    setResult(null);
    try {
      const res = await fetch('http://localhost:8000/ui/assign-token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token: form.token,
          merchant_id: form.merchant_id,
          amount: parseFloat(form.amount || 0),
          token_age_minutes: Number(form.token_age_minutes),
          device_trust_score: Number(form.device_trust_score),
          usual_location: form.usual_location,
          current_location: form.current_location,
          new_device: form.new_device,
          vpn_detected: form.vpn_detected,
          unusual_time: form.unusual_time,
          rushed_transaction: form.rushed_transaction
        })
      });

      const data = await res.json();
      setResult(data);
    } catch (err) {
      setResult({ error: String(err) });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="App-root">
      <Header />
      <NavTabs />
      <main className="container">
        <h1 className="title">Transaction Risk Analysis</h1>
        <p className="subtitle">Analyze transaction risk with AI-powered intelligence</p>

        <div className="grid">
          <section className="card left">
            <h3>Transaction Details</h3>
            <label>Token ID</label>
            <input value={form.token} onChange={e => update('token', e.target.value)} placeholder="tok_xxx" />

            <label>Merchant ID</label>
            <input value={form.merchant_id} onChange={e => update('merchant_id', e.target.value)} placeholder="merchant_store" />

            <label>Amount (₹)</label>
            <input value={form.amount} onChange={e => update('amount', e.target.value)} placeholder="1300" />
          </section>

          <section className="card right">
            <h3>Security Context</h3>
            <label>Device Trust Score</label>
            <input type="range" min="0" max="1" step="0.01" value={form.device_trust_score} onChange={e => update('device_trust_score', e.target.value)} />
            <div className="score">{Math.round(form.device_trust_score * 100)}%</div>

            <div className="row">
              <div>
                <label>Token Age (minutes)</label>
                <input value={form.token_age_minutes} onChange={e => update('token_age_minutes', e.target.value)} />
              </div>
              <div>
                <label>Usual Location</label>
                <input value={form.usual_location} onChange={e => update('usual_location', e.target.value)} placeholder="Mumbai" />
              </div>
            </div>

            <label>Current Location</label>
            <input value={form.current_location} onChange={e => update('current_location', e.target.value)} placeholder="Mumbai" />

            <div className="checkboxes">
              <label><input type="checkbox" checked={form.new_device} onChange={e => update('new_device', e.target.checked)} /> New Device</label>
              <label><input type="checkbox" checked={form.vpn_detected} onChange={e => update('vpn_detected', e.target.checked)} /> Vpn Detected</label>
              <label><input type="checkbox" checked={form.unusual_time} onChange={e => update('unusual_time', e.target.checked)} /> Unusual Time</label>
              <label><input type="checkbox" checked={form.rushed_transaction} onChange={e => update('rushed_transaction', e.target.checked)} /> Rushed Transaction</label>
            </div>
          </section>
        </div>

        <div className="actions">
          <button className="primary" onClick={assignToken} disabled={loading}>{loading ? 'Processing…' : 'Assign Token'}</button>
          <button className="secondary" onClick={() => setForm({ ...form, token: 'tok_' + Math.random().toString(36).slice(2, 10) })}>Generate Token ID</button>
        </div>

        {result && (
          <div className="result">
            <h4>Result</h4>
            <pre>{JSON.stringify(result, null, 2)}</pre>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
