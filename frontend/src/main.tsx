import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import PlotComponent from 'react-plotly.js';
import { Bot, Building2, ChartNoAxesCombined, FileUp, ShieldAlert, Sparkles } from 'lucide-react';
import './styles.css';

const Plot = (PlotComponent as any).default || PlotComponent;
const api = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';
type Page = 'Dashboard' | 'Upload Report' | 'AI Chatbot' | 'Forecasting' | 'Competitors' | 'Risk Analysis' | 'Market Sentiment' | 'Recommendation';
type Metrics = { revenue: number; net_income: number; assets: number; liabilities: number; operating_cash_flow: number; revenue_history: number[] };
type Report = { report_id: string; filename: string; pages: number; chunks_indexed: number; preliminary_metrics: Metrics; latest_fiscal_year: number | null };
const nav: Page[] = ['Dashboard', 'Upload Report', 'AI Chatbot', 'Forecasting', 'Competitors', 'Risk Analysis', 'Market Sentiment', 'Recommendation'];

function Card({ title, value, detail }: { title: string; value: string; detail: string }) {
  return <section className="card"><p>{title}</p><h2>{value}</h2><small>{detail}</small></section>;
}

async function postJSON(path: string, body: unknown) {
  const response = await fetch(`${api}${path}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail ?? 'Request failed.');
  return data;
}

function withHistory(metrics: Metrics): Metrics {
  return metrics.revenue_history.length >= 2 ? metrics : { ...metrics, revenue_history: [metrics.revenue, metrics.revenue] };
}

const DEFAULT_SENTIMENT_TEXT = 'Strong quarterly earnings beat analyst expectations.\nRegulatory scrutiny raises concerns about future growth.';

async function fetchReportExcerpts(reportId: string): Promise<string> {
  const response = await fetch(`${api}/api/v1/reports/${reportId}/excerpts`);
  if (!response.ok) return DEFAULT_SENTIMENT_TEXT;
  const data = await response.json();
  const excerpts: string[] = data.excerpts ?? [];
  return excerpts.length ? excerpts.map(e => e.replace(/\s+/g, ' ').trim()).join('\n') : DEFAULT_SENTIMENT_TEXT;
}

function health(metrics: Metrics) {
  if (!metrics.assets) return 0;
  const debt = metrics.liabilities / metrics.assets;
  const margin = metrics.revenue ? metrics.net_income / metrics.revenue : 0;
  return Math.max(0, Math.min(100, Math.round(65 - debt * 25 + margin * 100)));
}

async function downloadReportPdf(report: Report) {
  const response = await fetch(`${api}/api/v1/reports/${report.report_id}/export/pdf`);
  if (!response.ok) { alert('PDF export failed.'); return; }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url; link.download = `${report.filename.replace(/\.pdf$/i, '')}-finsight-report.pdf`;
  link.click(); URL.revokeObjectURL(url);
}

function Dashboard({ report }: { report: Report | null }) {
  if (!report) return <main className="center"><ChartNoAxesCombined size={42}/><h1>Your dashboard is ready for a report</h1><p>Upload an annual report to see extracted metrics and export an analysis file.</p></main>;
  const metrics = report.preliminary_metrics;
  const chartValues = [metrics.revenue, metrics.net_income, metrics.assets, metrics.liabilities, metrics.operating_cash_flow];
  return <><div className="heading"><div><p className="eyebrow">UPLOADED REPORT</p><h1>{report.filename}</h1><p>{report.pages} pages indexed into {report.chunks_indexed} knowledge chunks</p></div><button onClick={() => downloadReportPdf(report)}>Export PDF</button></div><div className="grid stats"><Card title="Revenue" value={metrics.revenue ? `$${metrics.revenue.toLocaleString()}` : 'Not detected'} detail="Preliminary extraction"/><Card title="Net income" value={metrics.net_income ? `$${metrics.net_income.toLocaleString()}` : 'Not detected'} detail="Preliminary extraction"/><Card title="Financial health" value={`${health(metrics)} / 100`} detail="Balance sheet estimate"/><Card title="Report status" value="Indexed" detail="Ready for RAG chat"/></div><div className="grid charts"><section className="card wide"><p>Extracted financial indicators</p><Plot data={[{ x: ['Revenue', 'Net income', 'Assets', 'Liabilities', 'Cash flow'], y: chartValues, type: 'bar', marker: { color: '#51e5b8' } }]} layout={{ autosize: true, height: 280, paper_bgcolor: 'transparent', plot_bgcolor: 'transparent', font: { color: '#c7d2e8' }, margin: { l: 55, r: 10, t: 15, b: 45 }, yaxis: { gridcolor: '#24324d' } }} config={{ displayModeBar: false }} /></section><section className="card"><p>AI insight</p><h3>Ask the report</h3><small>Use the AI Chatbot page for grounded answers with page references from this uploaded report.</small></section></div></>;
}

function Upload({ reports, onUploaded, onSelect, openDashboard }: { reports: Report[]; onUploaded: (report: Report) => void; onSelect: (id: string) => void; openDashboard: () => void }) {
  const [message, setMessage] = useState('');
  const [ready, setReady] = useState(false);
  async function upload(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]; if (!file) return;
    const form = new FormData(); form.append('file', file); setReady(false); setMessage('Indexing annual report…');
    try {
      const response = await fetch(`${api}/api/v1/reports/upload`, { method: 'POST', body: form });
      const data = await response.json(); if (!response.ok) throw new Error(data.detail);
      onUploaded(data); setReady(true); setMessage(`${data.filename}: ${data.pages} pages and ${data.chunks_indexed} knowledge chunks are ready.`);
    } catch (error) { setMessage(error instanceof Error ? error.message : 'Upload failed.'); }
  }
  return <main className="center"><FileUp size={42}/><h1>Upload an annual report</h1><p>Each upload is kept, so you can switch between reports or compare several on the Competitors page.</p><label className="upload">Choose PDF<input type="file" accept="application/pdf" onChange={upload}/></label><small>{message}</small>{ready && <button onClick={openDashboard}>View dashboard results</button>}{reports.length > 0 && <section className="card wide"><p>Previously uploaded ({reports.length})</p>{reports.map(r => <div className="checkbox-row" key={r.report_id}><span>{r.filename}</span><button onClick={() => { onSelect(r.report_id); openDashboard(); }}>View</button></div>)}</section>}</main>;
}

function Chat({ report }: { report: Report | null }) {
  const [question, setQuestion] = useState('Summarize the financial performance.'); const [answer, setAnswer] = useState('');
  async function ask() {
    if (!report) { setAnswer('Upload a report first.'); return; }
    try { const response = await fetch(`${api}/api/v1/chat`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ report_id: report.report_id, question }) }); const data = await response.json(); setAnswer(response.ok ? `${data.answer}\n\nSources: ${data.sources?.map((source: { page: number }) => `page ${source.page}`).join(', ')}` : data.detail); } catch { setAnswer('Unable to reach the API.'); }
  }
  return <main className="chat"><div><p className="eyebrow">RAG ANALYST</p><h1>Ask the annual report</h1><p>{report ? `Using ${report.filename}` : 'Upload a report first.'}</p></div><textarea value={question} onChange={event => setQuestion(event.target.value)}/><button onClick={ask}>Ask FinSight</button><pre>{answer || 'Ask a question to receive a cited answer.'}</pre></main>;
}

type RiskResult = { risk_score: number; risk_level: string; debt_ratio: number; revenue_growth_pct: number; explanation: string };
type ForecastResult = { forecast: number[]; lower_bound: number[]; upper_bound: number[]; forecast_years: number[]; trend: string; latest_revenue: number; growth_opportunity: string };
type SentimentResult = { sentiment: string; confidence: number; items: { label: string; confidence: number }[] };
type RecommendationResult = { risk: RiskResult; revenue: ForecastResult; sentiment: SentimentResult; health_score: number; recommendation: { recommendation: string; investment_score: number; reasoning: string } };
type CompetitorRow = { company: string; revenue: number; net_income: number; assets: number; liabilities: number; operating_cash_flow: number };
type CompetitorResult = { companies: { company: string; revenue: number; net_income: number; risk_score: number; growth_pct: number; health_score: number }[]; leader: string };

function RiskAnalysis({ report }: { report: Report | null }) {
  const [result, setResult] = useState<RiskResult | null>(null);
  const [error, setError] = useState('');
  useEffect(() => {
    setResult(null); setError('');
    if (!report) return;
    postJSON('/api/v1/analysis/risk', report.preliminary_metrics).then(setResult).catch(err => setError(err.message));
  }, [report]);
  if (!report) return <main className="center"><ShieldAlert size={42}/><h1>Upload a report to run risk analysis</h1><p>Risk scoring uses the balance-sheet metrics extracted from your uploaded report.</p></main>;
  if (error) return <main className="center"><ShieldAlert size={42}/><h1>Risk analysis failed</h1><p>{error}</p></main>;
  if (!result) return <main className="center"><ShieldAlert size={42}/><h1>Scoring risk…</h1></main>;
  return <><div className="heading"><div><p className="eyebrow">RISK ANALYSIS AGENT</p><h1>{result.risk_level} risk</h1><p>{report.filename}</p></div></div><div className="grid stats"><Card title="Risk score" value={`${result.risk_score} / 100`} detail="Weighted balance-sheet & cash-flow score"/><Card title="Risk level" value={result.risk_level} detail="Low / Medium / High"/><Card title="Debt ratio" value={`${(result.debt_ratio * 100).toFixed(1)}%`} detail="Liabilities / assets"/><Card title="Revenue trend" value={`${result.revenue_growth_pct.toFixed(1)}%`} detail="Period-over-period change"/></div><section className="card wide"><p>Explanation</p><h3>{result.explanation}</h3></section></>;
}

function Forecasting({ report }: { report: Report | null }) {
  const [result, setResult] = useState<ForecastResult | null>(null);
  const [error, setError] = useState('');
  useEffect(() => {
    setResult(null); setError('');
    if (!report) return;
    const path = `/api/v1/analysis/forecast${report.latest_fiscal_year ? `?latest_year=${report.latest_fiscal_year}` : ''}`;
    postJSON(path, withHistory(report.preliminary_metrics)).then(setResult).catch(err => setError(err.message));
  }, [report]);
  if (!report) return <main className="center"><ChartNoAxesCombined size={42}/><h1>Upload a report to forecast revenue</h1><p>Forecasts use Prophet when enough revenue history is available.</p></main>;
  if (error) return <main className="center"><ChartNoAxesCombined size={42}/><h1>Forecast failed</h1><p>{error}</p></main>;
  if (!result) return <main className="center"><ChartNoAxesCombined size={42}/><h1>Forecasting revenue…</h1></main>;
  const usingRealHistory = report.preliminary_metrics.revenue_history.length >= 2;
  const periods = result.forecast_years.map(String);
  return <><div className="heading"><div><p className="eyebrow">REVENUE FORECASTING AGENT</p><h1>Revenue is {result.trend}</h1><p>{report.filename}{!usingRealHistory && ' — only one fiscal year of revenue was extractable, so this forecast is a flat placeholder rather than a real trend.'}</p></div></div><div className="grid stats"><Card title="Latest revenue" value={`$${result.latest_revenue.toLocaleString()}`} detail={`Fiscal ${report.latest_fiscal_year ?? 'year'}`}/><Card title={`${periods[0]} forecast`} value={`$${result.forecast[0].toLocaleString()}`} detail="Model prediction"/><Card title="Trend" value={result.trend} detail={result.growth_opportunity}/><Card title="Forecast band" value={`±$${Math.round((result.upper_bound[0] - result.lower_bound[0]) / 2).toLocaleString()}`} detail={`Uncertainty at ${periods[0]}`}/></div><section className="card wide"><p>Forecast trajectory ({periods[0]}–{periods[periods.length - 1]})</p><Plot data={[{ x: periods, y: result.forecast, type: 'scatter', mode: 'lines+markers', name: 'Forecast', line: { color: '#51e5b8' } }, { x: periods, y: result.upper_bound, type: 'scatter', mode: 'lines', name: 'Upper bound', line: { color: '#31425e', dash: 'dot' } }, { x: periods, y: result.lower_bound, type: 'scatter', mode: 'lines', name: 'Lower bound', line: { color: '#31425e', dash: 'dot' } }]} layout={{ autosize: true, height: 300, paper_bgcolor: 'transparent', plot_bgcolor: 'transparent', font: { color: '#c7d2e8' }, margin: { l: 55, r: 10, t: 15, b: 45 }, yaxis: { gridcolor: '#24324d' }, legend: { orientation: 'h' } }} config={{ displayModeBar: false }} /></section></>;
}

function sentimentBreakdown(items: { label: string; confidence: number }[], sourceTexts: string[]) {
  return items.map((item, i) => {
    const source = (sourceTexts[i] ?? '').replace(/\s+/g, ' ').trim();
    const snippet = source.length > 160 ? `${source.slice(0, 160)}…` : source;
    return `${i + 1}. [${item.label.toUpperCase()} · ${Math.round(item.confidence * 100)}% confidence]\n   "${snippet}"`;
  }).join('\n\n');
}

function MarketSentiment({ report }: { report: Report | null }) {
  const [text, setText] = useState(DEFAULT_SENTIMENT_TEXT);
  const [analyzedTexts, setAnalyzedTexts] = useState<string[]>([]);
  const [result, setResult] = useState<SentimentResult | null>(null);
  const [error, setError] = useState('');
  useEffect(() => {
    if (!report) { setText(DEFAULT_SENTIMENT_TEXT); return; }
    fetchReportExcerpts(report.report_id).then(setText);
  }, [report]);
  async function analyze() {
    const texts = text.split('\n').map(line => line.trim()).filter(Boolean);
    if (!texts.length) { setError('Add at least one headline or note.'); return; }
    setError(''); setResult(null);
    try { setResult(await postJSON('/api/v1/analysis/sentiment', { texts })); setAnalyzedTexts(texts); }
    catch (err) { setError(err instanceof Error ? err.message : 'Sentiment analysis failed.'); }
  }
  return <main className="chat"><div><p className="eyebrow">MARKET SENTIMENT AGENT</p><h1>Analyze financial news & commentary</h1><p>{report ? `Pre-filled with real excerpts from ${report.filename} — edit or paste your own headlines.` : 'Paste one headline, analyst note, or news snippet per line.'}</p></div><textarea value={text} onChange={event => setText(event.target.value)}/><button onClick={analyze}>Analyze sentiment</button>{error && <pre>{error}</pre>}{result && <><div className="grid stats"><Card title="Overall sentiment" value={result.sentiment} detail="Majority label across inputs"/><Card title="Confidence" value={`${Math.round(result.confidence * 100)}%`} detail="Average model confidence"/></div><p>Per-item breakdown — which input each score belongs to:</p><pre>{sentimentBreakdown(result.items, analyzedTexts)}</pre></>}</main>;
}

function Recommendation({ report }: { report: Report | null }) {
  const [text, setText] = useState(DEFAULT_SENTIMENT_TEXT);
  const [analyzedTexts, setAnalyzedTexts] = useState<string[]>([]);
  const [result, setResult] = useState<RecommendationResult | null>(null);
  const [error, setError] = useState('');
  useEffect(() => {
    if (!report) { setText(DEFAULT_SENTIMENT_TEXT); return; }
    fetchReportExcerpts(report.report_id).then(setText);
  }, [report]);
  async function run() {
    if (!report) return;
    const texts = text.split('\n').map(line => line.trim()).filter(Boolean);
    setError(''); setResult(null);
    try {
      setResult(await postJSON('/api/v1/analysis/recommendation', { metrics: withHistory(report.preliminary_metrics), sentiment_texts: texts.length ? texts : undefined, latest_year: report.latest_fiscal_year }));
      setAnalyzedTexts(texts);
    } catch (err) { setError(err instanceof Error ? err.message : 'Recommendation failed.'); }
  }
  if (!report) return <main className="center"><Sparkles size={42}/><h1>Upload a report for an investment recommendation</h1><p>Combines the risk, forecast, and sentiment agents into one verdict.</p></main>;
  return <main className="chat"><div><p className="eyebrow">INVESTMENT RECOMMENDATION AGENT</p><h1>Combine every signal into one verdict</h1><p>Using {report.filename}, pre-filled with real excerpts from this report — edit as needed.</p></div><textarea value={text} onChange={event => setText(event.target.value)}/><button onClick={run}>Generate recommendation</button>{error && <pre>{error}</pre>}{result && <><div className="grid stats"><Card title="Recommendation" value={result.recommendation.recommendation} detail={`Score ${result.recommendation.investment_score} / 100`}/><Card title="Financial health" value={`${result.health_score} / 100`} detail="Balance sheet estimate"/><Card title="Risk" value={result.risk.risk_level} detail={`${result.risk.risk_score} / 100`}/><Card title="Sentiment" value={result.sentiment.sentiment} detail={`${Math.round(result.sentiment.confidence * 100)}% confidence`}/></div><section className="card wide"><p>Reasoning</p><h3>{result.recommendation.reasoning}</h3></section><section className="card wide"><p>Sentiment inputs — which excerpt drove each score</p><pre>{sentimentBreakdown(result.sentiment.items, analyzedTexts)}</pre></section></>}</main>;
}

function emptyCompetitor(name: string): CompetitorRow { return { company: name, revenue: 0, net_income: 0, assets: 0, liabilities: 0, operating_cash_flow: 0 }; }

function Competitors({ reports }: { reports: Report[] }) {
  const [selected, setSelected] = useState<string[]>(() => reports.slice(-2).map(r => r.report_id));
  const [rows, setRows] = useState<CompetitorRow[]>([]);
  const [result, setResult] = useState<CompetitorResult | null>(null);
  const [error, setError] = useState('');
  function toggleSelected(id: string) { setSelected(sel => sel.includes(id) ? sel.filter(x => x !== id) : [...sel, id]); }
  function updateRow(index: number, field: keyof CompetitorRow, value: string) {
    setRows(rows.map((row, i) => i === index ? { ...row, [field]: field === 'company' ? value : Number(value) || 0 } : row));
  }
  function addRow() { if (rows.length < 4) setRows([...rows, emptyCompetitor(`Competitor ${String.fromCharCode(65 + rows.length)}`)]); }
  function removeRow(index: number) { setRows(rows.filter((_, i) => i !== index)); }
  async function compare() {
    const companies: Record<string, Metrics> = {};
    reports.filter(r => selected.includes(r.report_id)).forEach(r => { companies[r.filename.replace(/\.pdf$/i, '')] = r.preliminary_metrics; });
    rows.forEach(row => { companies[row.company || 'Competitor'] = { revenue: row.revenue, net_income: row.net_income, assets: row.assets, liabilities: row.liabilities, operating_cash_flow: row.operating_cash_flow, revenue_history: [] }; });
    if (Object.keys(companies).length < 2) { setError('Select at least two uploaded reports, or add a manual competitor, to compare.'); return; }
    setError(''); setResult(null);
    try { setResult(await postJSON('/api/v1/analysis/competitors', { companies })); }
    catch (err) { setError(err instanceof Error ? err.message : 'Comparison failed.'); }
  }
  if (!reports.length && !rows.length) return <main className="center"><Building2 size={42}/><h1>Upload at least one report to compare competitors</h1><p>Upload two or more annual reports and select them here, or add a competitor's metrics manually.</p></main>;
  return <><div className="heading"><div><p className="eyebrow">COMPETITOR ANALYSIS AGENT</p><h1>Benchmark uploaded reports</h1><p>Select two or more uploaded reports, or add a competitor manually.</p></div><button onClick={compare}>Compare</button></div>{reports.length > 0 && <section className="card wide"><p>Uploaded reports</p>{reports.map(r => <div className="checkbox-row" key={r.report_id}><label><input type="checkbox" checked={selected.includes(r.report_id)} onChange={() => toggleSelected(r.report_id)}/>{r.filename}</label></div>)}</section>}{rows.map((row, index) => <section className="card wide" key={index}><div className="heading"><p>Manual competitor {index + 1}</p><button onClick={() => removeRow(index)}>Remove</button></div><div className="grid form-grid"><input className="field" value={row.company} onChange={e => updateRow(index, 'company', e.target.value)} placeholder="Company name"/><input className="field" value={row.revenue || ''} onChange={e => updateRow(index, 'revenue', e.target.value)} placeholder="Revenue"/><input className="field" value={row.net_income || ''} onChange={e => updateRow(index, 'net_income', e.target.value)} placeholder="Net income"/><input className="field" value={row.assets || ''} onChange={e => updateRow(index, 'assets', e.target.value)} placeholder="Assets"/><input className="field" value={row.liabilities || ''} onChange={e => updateRow(index, 'liabilities', e.target.value)} placeholder="Liabilities"/><input className="field" value={row.operating_cash_flow || ''} onChange={e => updateRow(index, 'operating_cash_flow', e.target.value)} placeholder="Operating cash flow"/></div></section>)}{rows.length < 4 && <button onClick={addRow}>+ Add manual competitor</button>}{error && <pre>{error}</pre>}{result && <section className="card wide"><p>Health score comparison</p><Plot data={[{ x: result.companies.map(c => c.company), y: result.companies.map(c => c.health_score), type: 'bar', marker: { color: '#51e5b8' } }]} layout={{ autosize: true, height: 260, paper_bgcolor: 'transparent', plot_bgcolor: 'transparent', font: { color: '#c7d2e8' }, margin: { l: 55, r: 10, t: 15, b: 45 }, yaxis: { gridcolor: '#24324d' } }} config={{ displayModeBar: false }} /><h3>Leader: {result.leader}</h3></section>}</>;
}

function App() {
  const [page, setPage] = useState<Page>('Dashboard');
  const [reports, setReports] = useState<Report[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  useEffect(() => {
    const stored = localStorage.getItem('finsight-reports');
    if (!stored) return;
    const parsed: Report[] = JSON.parse(stored);
    setReports(parsed);
    if (parsed.length) setActiveId(parsed[parsed.length - 1].report_id);
  }, []);
  function onUploaded(newReport: Report) {
    setReports(prev => {
      const next = [...prev, newReport];
      localStorage.setItem('finsight-reports', JSON.stringify(next));
      return next;
    });
    setActiveId(newReport.report_id);
  }
  function removeReport(id: string) {
    setReports(prev => {
      const next = prev.filter(r => r.report_id !== id);
      localStorage.setItem('finsight-reports', JSON.stringify(next));
      if (activeId === id) setActiveId(next.length ? next[next.length - 1].report_id : null);
      return next;
    });
  }
  const report = reports.find(r => r.report_id === activeId) ?? null;
  const content = page === 'Dashboard' ? <Dashboard report={report}/>
    : page === 'Upload Report' ? <Upload reports={reports} onUploaded={onUploaded} onSelect={setActiveId} openDashboard={() => setPage('Dashboard')}/>
    : page === 'AI Chatbot' ? <Chat report={report}/>
    : page === 'Risk Analysis' ? <RiskAnalysis report={report}/>
    : page === 'Forecasting' ? <Forecasting report={report}/>
    : page === 'Market Sentiment' ? <MarketSentiment report={report}/>
    : page === 'Recommendation' ? <Recommendation report={report}/>
    : <Competitors reports={reports}/>;
  return <div className="app"><aside><div className="brand"><Building2/> FinSight <i>AI</i></div><nav>{nav.map(item => <button className={item === page ? 'active' : ''} onClick={() => setPage(item)} key={item}>{item === 'Dashboard' ? <ChartNoAxesCombined/> : item === 'Risk Analysis' ? <ShieldAlert/> : item === 'AI Chatbot' ? <Bot/> : <span/>}{item}</button>)}</nav>{reports.length > 0 && <div className="sidebar-reports"><p className="eyebrow">ACTIVE REPORT</p><select className="field" value={activeId ?? ''} onChange={e => setActiveId(e.target.value)}>{reports.map(r => <option key={r.report_id} value={r.report_id}>{r.filename}</option>)}</select>{activeId && <button onClick={() => removeReport(activeId)}>Remove this report</button>}</div>}<div className="profile">ANALYST WORKSPACE<br/><small>Production demo</small></div></aside><article>{content}</article></div>;
}

createRoot(document.getElementById('root')!).render(<App/>);
