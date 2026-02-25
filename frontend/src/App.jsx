import React, { useState, useEffect } from 'react';
import './App.css';
import RefreshIcon from './assets/refresh.svg';

const API_BASE = 'http://localhost:8000';

function App() {
  const [files, setFiles] = useState([]);
  const [reports, setReports] = useState([]);
  const [weeklyReport, setWeeklyReport] = useState(null);
  const [topPerformers, setTopPerformers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);
  const [activeTab, setActiveTab] = useState('generate');
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [password, setPassword] = useState('');
  const [perfBranch, setPerfBranch] = useState('OVERALL');
  const [perfTopN, setPerfTopN] = useState(50);
  const [performanceViewActive, setPerformanceViewActive] = useState(false);

  useEffect(() => {
    if (isLoggedIn) {
      fetchHistory();
    }
  }, [isLoggedIn]);

  const fetchHistory = async () => {
    try {
      const res = await fetch(`${API_BASE}/history`);
      const data = await res.json();
      setHistory(data);
    } catch (err) {
      console.error('Failed to fetch history', err);
    }
  };

  const handleLogin = (e) => {
    e.preventDefault();
    if (password === 'cit') {
      setIsLoggedIn(true);
    } else {
      alert('Incorrect password');
    }
  };

  const handleFileChange = (e) => {
    setFiles(Array.from(e.target.files));
  };

  const handleUpload = async () => {
    if (files.length === 0) return;
    setLoading(true);
    const formData = new FormData();
    files.forEach(f => formData.append('files', f));

    try {
      const res = await fetch(`${API_BASE}/process`, {
        method: 'POST',
        body: formData
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Upload failed');
      }
      const data = await res.json();
      setReports(data);
      setWeeklyReport(null);
      setTopPerformers([]);
      setPerformanceViewActive(false);
      fetchHistory();
    } catch (err) {
      alert('Upload failed: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleWeeklyAnalysis = async () => {
    if (files.length === 0) return;
    setLoading(true);
    const formData = new FormData();
    files.forEach(f => formData.append('files', f));

    try {
      const res = await fetch(`${API_BASE}/weekly`, {
        method: 'POST',
        body: formData
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Weekly analysis failed');
      }
      const data = await res.json();
      setWeeklyReport(data);
      setReports([]);
      setTopPerformers([]);
      setPerformanceViewActive(false);
    } catch (err) {
      alert('Weekly analysis failed: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handlePerformanceAnalysis = async () => {
    if (files.length === 0) return;
    setLoading(true);
    const formData = new FormData();
    files.forEach(f => formData.append('files', f));
    formData.append('top_n', perfTopN);
    formData.append('branch', perfBranch);

    try {
      const res = await fetch(`${API_BASE}/performance`, {
        method: 'POST',
        body: formData
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Performance analysis failed');
      }
      const data = await res.json();
      console.log('Performance result:', data);
      setTopPerformers(Array.isArray(data) ? data : []);
      setReports([]);
      setWeeklyReport(null);
      setPerformanceViewActive(true);
    } catch (err) {
      alert('Performance analysis failed: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = (type) => {
    try {
      window.open(`${API_BASE}/download/${type}`, '_blank');
    } catch (err) {
      alert(`Download ${type} failed`);
    }
  };

  if (!isLoggedIn) {
    return (
      <div className="container animate-fade" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <div className="glass-card" style={{ width: '400px', textAlign: 'center' }}>
          <h2>Access Restricted</h2>
          <p style={{ margin: '1rem 0', color: 'var(--secondary-text)' }}>Please enter the password to continue.</p>
          <form onSubmit={handleLogin}>
            <input
              type="password"
              style={{
                width: '100%',
                marginBottom: '1rem',
                textAlign: 'center',
                background: 'var(--bg-color)',
                color: 'var(--text-color)',
                border: '1px solid var(--border-color)',
                borderRadius: '8px',
                padding: '0.8rem',
                outline: 'none'
              }}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password"
            />
            <button type="submit" className="btn" style={{ width: '100%' }}>Login</button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="app-layout animate-fade">

      <aside className="sidebar">
        <header style={{ display: 'flex', alignItems: 'center', marginBottom: '0.5rem' }}>
          <h1>Skill Rack</h1>
          <button className="refresh-btn" title="Clear for new analysis" onClick={() => { setFiles([]); setReports([]); setWeeklyReport(null); setTopPerformers([]); setPerformanceViewActive(false); }}>
            <img src={RefreshIcon} alt="Refresh" />
          </button>
        </header>
        <p className="subtitle">Result Analysis Automation</p>

        <div className="tabs" style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
          <button
            className={`btn ${activeTab === 'generate' ? '' : 'btn-secondary'}`}
            style={{ padding: '0.5rem' }}
            onClick={() => { setActiveTab('generate'); setWeeklyReport(null); setTopPerformers([]); setPerformanceViewActive(false); }}
          >
            Generate
          </button>
          <button
            className={`btn ${activeTab === 'history' ? '' : 'btn-secondary'}`}
            style={{ padding: '0.5rem' }}
            onClick={() => setActiveTab('history')}
          >
            History
          </button>
        </div>

        {activeTab === 'generate' && (
          <div className="glass-card">
            <h3>Upload Results</h3>
            <p style={{ color: 'var(--secondary-text)', marginBottom: '1rem', fontSize: '0.8rem' }}>
              Upload CSV or Excel files.
            </p>

            <div className="upload-zone" onClick={() => document.getElementById('fileInput').click()}>
              {files.length > 0 ? (
                <div>
                  <strong>{files.length} files selected</strong>
                  <ul style={{ listStyle: 'none', marginTop: '0.5rem', fontSize: '0.7rem', maxHeight: '100px', overflowY: 'auto' }}>
                    {files.map(f => <li key={f.name}>{f.name}</li>)}
                  </ul>
                </div>
              ) : (
                <p style={{ fontSize: '0.8rem' }}>Click or Drop Files</p>
              )}
              <input
                id="fileInput"
                type="file"
                multiple
                hidden
                onChange={handleFileChange}
                accept=".csv, .xlsx, .xls"
              />
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <button
                className="btn"
                onClick={handleUpload}
                disabled={loading || files.length === 0}
              >
                {loading ? 'Processing...' : 'Run Daily Analysis'}
              </button>
              <button
                className="btn btn-secondary"
                onClick={handleWeeklyAnalysis}
                disabled={loading || files.length === 0}
              >
                Weekly Analysis
              </button>
            </div>

            <div style={{ marginTop: '1.5rem', paddingTop: '1.5rem', borderTop: '1px solid var(--border-color)' }}>
              <button
                className="btn btn-secondary"
                onClick={() => {
                  setReports([]);
                  setWeeklyReport(null);
                  setTopPerformers([]);
                  setPerformanceViewActive(true);
                  handlePerformanceAnalysis();
                }}
              >
                Top Performers Analysis
              </button>
            </div>

            {(reports.length > 0 || weeklyReport || (Array.isArray(topPerformers) && topPerformers.length > 0)) && (
              <div style={{ marginTop: '1rem', fontSize: '0.8rem', color: 'var(--secondary-text)', textAlign: 'center' }}>
                Download options are now below the results.
              </div>
            )}
          </div>
        )}


        <button
          className="btn btn-secondary"
          style={{ fontSize: '0.7rem', marginTop: 'auto', position: 'absolute', bottom: '2rem', left: '2rem', width: 'calc(400px - 4rem)' }}
          onClick={() => setIsLoggedIn(false)}
        >
          Logout
        </button>
      </aside>

      <main className="content-area">
        {activeTab !== 'history' && !reports.length && !weeklyReport && (!Array.isArray(topPerformers) || !topPerformers.length) && !performanceViewActive && (
          <div style={{ height: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', color: 'var(--secondary-text)' }}>
            <p>Upload files on the left to see results here.</p>
          </div>
        )}

        {performanceViewActive && (
          <div className="glass-card animate-fade" style={{ marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3 style={{ margin: 0 }}> Top Performers Curation</h3>
              <button
                className="btn btn-secondary"
                style={{ width: 'auto', padding: '0.4rem 1rem' }}
                onClick={handlePerformanceAnalysis}
                disabled={loading}
              >
                {loading ? 'Analyzing...' : 'Refresh Rankings'}
              </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
              <div>
                <label style={{ fontSize: '0.8rem', color: 'var(--secondary-text)', display: 'block', marginBottom: '0.5rem' }}>Department Filter</label>
                <select
                  className="btn btn-secondary"
                  style={{ background: 'var(--bg-color)', width: '100%', textAlign: 'left', padding: '0.6rem' }}
                  value={perfBranch}
                  onChange={(e) => setPerfBranch(e.target.value)}
                >
                  <option value="OVERALL">OVERALL</option>
                  <option value="CSE">CSE</option>
                  <option value="ECE">ECE</option>
                  <option value="EEE">EEE</option>
                  <option value="MECH">MECH</option>
                  <option value="IT">IT</option>
                  <option value="AIDS">AIDS</option>
                  <option value="AIML">AIML</option>
                  <option value="CIVIL">CIVIL</option>
                  <option value="MCT">MCT</option>
                  <option value="BIOMED">BIOMED</option>
                  <option value="CSBS">CSBS</option>
                  <option value="ACT">ACT</option>
                  <option value="VLSI">VLSI</option>
                </select>
              </div>
              <div>
                <label style={{ fontSize: '0.8rem', color: 'var(--secondary-text)', display: 'block', marginBottom: '0.5rem' }}>Show Top {perfTopN}</label>
                <input
                  type="range"
                  min="10"
                  max="500"
                  step="10"
                  style={{ width: '100%', marginTop: '0.5rem' }}
                  value={perfTopN}
                  onChange={(e) => setPerfTopN(parseInt(e.target.value))}
                />
              </div>
            </div>
          </div>
        )}

        {performanceViewActive && loading && (!Array.isArray(topPerformers) || !topPerformers.length) && (
          <div style={{ padding: '4rem', textAlign: 'center', color: 'var(--secondary-text)' }}>
            <p>Analyzing performance data, please wait...</p>
          </div>
        )}

        {reports.length > 0 && reports.map((rep, idx) => (
          <div key={idx} className="glass-card animate-fade">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h2 style={{ fontSize: '1.2rem' }}>Report: {rep.date}</h2>
              <span style={{ fontSize: '0.8rem', color: 'var(--secondary-text)' }}>{rep.years_text}</span>
            </div>

            <div className="data-table-container">
              <table>
                <thead>
                  <tr>
                    <th>Branch</th>
                    <th>Year</th>
                    <th>Registered</th>
                    <th>Appeared</th>
                    <th>Absent</th>
                    <th>Zero</th>
                    <th>One</th>
                    <th>Two</th>
                    <th>Three+</th>
                  </tr>
                </thead>
                <tbody>
                  {rep.data.map((row, ridx) => (
                    <tr key={ridx} style={{ fontWeight: row.Branch.includes('TOTAL') ? 'bold' : 'normal' }}>
                      <td>{row.Branch}</td>
                      <td>{row.Year}</td>
                      <td>{row["No of Registered Students"]}</td>
                      <td>{row["No of Students Appeared"]}</td>
                      <td>{row["No of Students Absent"]}</td>
                      <td>{row["Zero Problems Solved"]}</td>
                      <td>{row["One Problem Solved"]}</td>
                      <td>{row["Two Problems Solved"]}</td>
                      <td>{row["Three Problems Solved"]}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <button
              className="btn"
              onClick={() => handleDownload('daily')}
              style={{ background: '#22c55e', marginTop: '1.5rem', width: 'auto', padding: '0.6rem 2rem' }}
            >
              Download Daily Analysis Excel
            </button>
          </div>
        ))}

        {weeklyReport && (
          <div className="glass-card animate-fade">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3> Weekly Leaderboard</h3>
            </div>
            <div className="data-table-container">
              <table>
                <thead>
                  <tr>
                    <th>Rank</th>
                    <th>Name</th>
                    <th>Branch</th>
                    <th>Year</th>
                    <th>Days</th>
                    <th>Solved</th>
                    <th>Submissions</th>
                  </tr>
                </thead>
                <tbody>
                  {weeklyReport.map((row, idx) => (
                    <tr key={idx}>
                      <td><strong>{idx + 1}</strong></td>
                      <td>{row.Name}</td>
                      <td>{row.Branch}</td>
                      <td>{row.Year}</td>
                      <td>{row["Days Appeared"]}</td>
                      <td style={{ fontWeight: 'bold' }}>{row["Total Solved"]}</td>
                      <td>{row["Total Submissions"]}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <button
              className="btn"
              onClick={() => handleDownload('weekly')}
              style={{ background: '#22c55e', marginTop: '1.5rem', width: 'auto', padding: '0.6rem 2rem' }}
            >
              Download Weekly Leaderboard Excel
            </button>
          </div>
        )}


        {Array.isArray(topPerformers) && topPerformers.length > 0 && (
          <div className="glass-card animate-fade">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <div>
                <h2 style={{ fontSize: '1.4rem' }}>🏆 Top {topPerformers.length} Performers</h2>
                <p style={{ fontSize: '0.8rem', color: 'var(--secondary-text)' }}>{perfBranch} Rankings</p>
              </div>
            </div>


            <div className="data-table-container">
              <table>
                <thead>
                  <tr>
                    <th>Rank</th>
                    <th>Reg No</th>
                    <th>Name</th>
                    <th>Branch</th>
                    <th>Year</th>
                    <th>Solved</th>
                    <th>Submissions</th>
                    <th>Active Util</th>
                  </tr>
                </thead>
                <tbody>
                  {topPerformers.map((row, idx) => {
                    const rank = idx + 1;
                    const rankColor = rank === 1 ? '#FFD700' : rank === 2 ? '#C0C0C0' : rank === 3 ? '#CD7F32' : 'transparent';
                    return (
                      <tr key={idx}>
                        <td>
                          <div style={{
                            width: '24px', height: '24px', borderRadius: '50%',
                            background: rankColor, display: 'flex', alignItems: 'center',
                            justifyContent: 'center', fontWeight: 'bold'
                          }}>
                            {rank}
                          </div>
                        </td>
                        <td style={{ fontWeight: '500', fontSize: '0.85rem' }}>{row["Reg No"] || 'N/A'}</td>
                        <td>{row.Name}</td>
                        <td>{row.Branch}</td>
                        <td>{row.Year}</td>
                        <td style={{ fontWeight: 'bold' }}>{row["Solved count"]}</td>
                        <td>{row["Total submissions"]}</td>
                        <td>{row["Active utilisation"] || row["Total Active Util"] || 'N/A'}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <button
              className="btn"
              onClick={() => handleDownload('performance')}
              style={{ background: '#22c55e', marginTop: '2rem', width: 'auto', padding: '0.6rem 2rem' }}
            >
              Download Top Performers Excel
            </button>
          </div>
        )}

        {performanceViewActive && !loading && (!Array.isArray(topPerformers) || topPerformers.length === 0) && (
          <div className="glass-card animate-fade" style={{ padding: '4rem', textAlign: 'center' }}>
            <h3>No Performers Found</h3>
            <p style={{ color: 'var(--secondary-text)', marginTop: '0.5rem' }}>
              Try selecting a different department or verify your uploaded data.
            </p>
          </div>
        )}

        {activeTab === 'history' && (
          <div className="glass-card">
            <h3>Recent Reports</h3>
            <div className="data-table-container">
              <table>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Students</th>
                    <th>Generated At</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map(h => (
                    <tr key={h.id}>
                      <td>{h.analysis_date}</td>
                      <td>{h.total_students}</td>
                      <td>{h.timestamp}</td>
                      <td>
                        <button
                          className="btn btn-secondary"
                          style={{ padding: '0.4rem 1rem', fontSize: '0.6rem', width: 'auto' }}
                          onClick={async () => {
                            const res = await fetch(`${API_BASE}/history/${h.id}`);
                            if (!res.ok) {
                              const errData = await res.json();
                              alert('Failed to load report: ' + (errData.detail || res.statusText));
                              return;
                            }
                            const data = await res.json();
                            setReports([{ date: h.analysis_date, data, years_text: 'Historical Record' }]);
                            setActiveTab('generate');
                            setWeeklyReport(null);
                          }}
                        >
                          View
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
