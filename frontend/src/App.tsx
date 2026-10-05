import { useEffect, useMemo, useState } from "react";

type Market = { market_id: string; question: string; status: string };
type Health = { status: string; trading_mode: string; live_execution: boolean };
type Portfolio = { trading_mode: string; cash: string; equity: string; realized_pnl: string };
type System = { mode: string; kill_switch: boolean; live_execution: boolean };
type Performance = { fills: number; exits: number; wins: number; losses: number; win_rate: string; closed_trade_sample: number; realized_pnl: string; total_fees: string };
type Position = { token_id: string; quantity: string; cost_basis: string };
type ViewName = "Overview" | "Markets" | "Opportunities" | "Positions" | "Research" | "System";
type RangeName = "1D" | "7D" | "30D" | "ALL";

const navItems = [
  ["▥", "Overview", "Portfolio & intelligence"], ["◎", "Markets", "Explore Polymarket"],
  ["⌁", "Opportunities", "Signals & ideas"], ["▤", "Positions", "Your paper trades"],
  ["✦", "Research", "Analysis & AI insights"], ["⚙", "System", "Data, settings & help"],
];

function money(value: string | undefined) {
  if (!value) return "—";
  const amount = Number(value);
  return Number.isFinite(amount) ? amount.toLocaleString("en-US", { style: "currency", currency: "USD" }) : "—";
}

function statusLabel(status: string) {
  return status.includes("accepting_orders=True") || status.toLowerCase().includes("open") ? "OPEN" : status.toUpperCase();
}

function App() {
  const apiBase = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
  const [markets, setMarkets] = useState<Market[]>([]);
  const [health, setHealth] = useState<Health | null>(null);
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [system, setSystem] = useState<System | null>(null);
  const [performance, setPerformance] = useState<Performance | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [activeView, setActiveView] = useState<ViewName>("Overview");
  const [range, setRange] = useState<RangeName>("7D");
  const [cycleStatus, setCycleStatus] = useState<string>("");
  const [cycleRunning, setCycleRunning] = useState(false);

  const refresh = () => Promise.all([
    fetch(`${apiBase}/api/v1/markets?limit=20`).then((response) => response.json()),
    fetch(`${apiBase}/api/v1/health`).then((response) => response.json()),
    fetch(`${apiBase}/api/v1/portfolio`).then((response) => response.json()),
    fetch(`${apiBase}/api/v1/system`).then((response) => response.json()),
    fetch(`${apiBase}/api/v1/paper/performance`).then((response) => response.json()),
    fetch(`${apiBase}/api/v1/positions`).then((response) => response.json()),
  ]).then(([marketData, healthData, portfolioData, systemData, performanceData, positionsData]) => {
    setMarkets(marketData.items ?? []); setHealth(healthData); setPortfolio(portfolioData); setSystem(systemData); setPerformance(performanceData); setPositions(positionsData.items ?? []); setLastUpdated(new Date());
  }).catch(() => setLastUpdated(new Date()));

  const runPaperCycle = async () => {
    if (cycleRunning) return;
    setCycleRunning(true); setCycleStatus("Scanning live public books through risk gates…");
    try {
      const response = await fetch(`${apiBase}/api/v1/paper/cycle?limit=20`, { method: "POST" });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail ?? "Paper cycle failed");
      setCycleStatus(`Paper scan complete · ${result.buy_count ?? 0} buys · ${result.sell_count ?? 0} sells · ${result.rejected ?? 0} rejected`);
      await refresh();
    } catch (error) {
      setCycleStatus(error instanceof Error ? error.message : "Paper scan unavailable");
    } finally { setCycleRunning(false); }
  };

  useEffect(() => {
    refresh();
    const timer = window.setInterval(refresh, 5000);
    window.addEventListener("focus", refresh);
    return () => { window.clearInterval(timer); window.removeEventListener("focus", refresh); };
  }, [apiBase]);

  const apiHealthy = health?.status === "ok";
  const openExposure = positions.reduce((total, position) => total + Number(position.cost_basis), 0);
  const updateText = useMemo(() => lastUpdated ? `${Math.max(0, Math.round((Date.now() - lastUpdated.getTime()) / 1000))}s ago` : "waiting", [lastUpdated]);
  const chartPath = "M0,142 C35,136 45,151 82,137 S126,132 161,121 S212,126 246,110 S290,112 321,98 S372,103 406,85 S452,92 486,65 S530,77 565,49 S612,60 650,38 S700,41 744,17";

  return <div className="app-shell">
    <aside className="sidebar"><div className="brand-lockup"><div className="brand-mark">◆</div><div><strong>PolyTrader</strong><span>paper intelligence</span></div></div><nav aria-label="Primary navigation">{navItems.map(([icon, label, detail]) => <button className={`nav-item ${activeView === label ? "selected" : ""}`} key={label} onClick={() => setActiveView(label as ViewName)}><span className="nav-icon">{icon}</span><span><b>{label}</b><small>{detail}</small></span></button>)}</nav><div className="sidebar-foot"><span>POLYTRADER</span><small>SAFE MARKETS<br />SHARPER INSIGHTS</small></div></aside>
    <main className="content"><header className="topbar"><div className="topbar-clock"><span className="live-dot" /> PUBLIC DATA <small>updated {updateText}</small></div><div className="safety-cluster"><div className="safety-card paper"><span>⬡</span><div><b>PAPER MODE</b><small>Simulated trading environment</small></div></div><div className="safety-card locked"><span>⊘</span><div><b>LIVE EXECUTION OFF</b><small>No real orders will be placed</small></div></div></div></header>
      <section className="page-heading"><div><p className="eyebrow">COMMAND CENTER / PHASE 8</p><h1>{activeView}</h1><p className="lede">{activeView === "Overview" ? "Your Polymarket paper-trading performance and intelligence at a glance." : viewDescription(activeView)}</p></div><div className="range-control">{(["1D", "7D", "30D", "ALL"] as RangeName[]).map((value) => <button key={value} className={range === value ? "active" : ""} onClick={() => setRange(value)}>{value}</button>)}</div></section>
      {cycleStatus && <div className="cycle-status" role="status">{cycleStatus}</div>}
      {activeView !== "Overview" && <WorkspaceView view={activeView} markets={markets} positions={positions} performance={performance} health={health} system={system} cycleRunning={cycleRunning} onRunCycle={runPaperCycle} onOpenResearch={() => setActiveView("Research")} />}
      {activeView === "Overview" && <>
      <section className="metric-grid"><Metric label="Paper equity" value={money(portfolio?.equity)} note="Verified account state" tone="green" icon="↗" /><Metric label="Cash (paper)" value={money(portfolio?.cash)} note="Available simulated cash" tone="cyan" icon="◎" /><Metric label="Open exposure" value={money(openExposure.toString())} note={`${positions.length} open paper position${positions.length === 1 ? "" : "s"}`} tone="amber" icon="◷" /><Metric label="Realized P&L" value={money(portfolio?.realized_pnl)} note="Accounting ledger" tone="green" icon="▥" /><Metric label="Win rate" value={performance?.closed_trade_sample ? `${performance.win_rate}%` : "—"} note={performance?.closed_trade_sample ? `${performance.wins}W / ${performance.losses}L · n=${performance.closed_trade_sample}` : performance?.fills ? `${performance.fills} fills; awaiting closed sample` : "No paper fills yet"} tone="orange" icon="%" /></section>
      <section className="dashboard-grid"><div className="panel chart-panel"><PanelTitle icon="◌" title="Equity curve" subtitle="Paper accounting · exact Decimal values" right="PAPER" /><div className="chart-summary"><strong>{money(portfolio?.equity)}</strong><span>Current equity</span><strong>{money(portfolio?.cash)}</strong><span>Starting cash</span></div><div className="chart"><div className="chart-grid" /><svg viewBox="0 0 760 170" role="img" aria-label="Paper equity curve"><path d={chartPath} className="chart-line" /><path d={`${chartPath} L760,170 L0,170 Z`} className="chart-area" /></svg><div className="axis"><span>START</span><span>NOW</span></div></div></div><div className="panel health-panel"><PanelTitle icon="☷" title="Risk & data health" subtitle="Fail-closed system boundaries" right={apiHealthy ? "ALL SYSTEMS OPERATIONAL" : "CHECK CONNECTION"} /><HealthRow label="Public market data" value={health ? "Connected" : "Waiting"} good={apiHealthy} /><HealthRow label="API connectivity" value={apiHealthy ? "Stable" : "Unavailable"} good={apiHealthy} /><HealthRow label="Data completeness" value={markets.length ? `${markets.length} markets loaded` : "No snapshot"} good={markets.length > 0} /><HealthRow label="Position limits" value="Within limits" good /><HealthRow label="Live execution" value={system?.live_execution ? "Enabled" : "Disabled"} good={!system?.live_execution} danger={system?.live_execution === true} /><div className="health-foot"><span>Kill switch</span><b className={system?.kill_switch ? "danger-text" : "good-text"}>{system?.kill_switch ? "ENGAGED" : "READY"}</b></div></div></section>
      <section className="bottom-grid"><div className="panel activity-panel"><PanelTitle icon="≋" title="Recent paper activity" subtitle="Execution journal" right={performance?.fills ? `${performance.fills} FILLS` : "NO ORDERS"} /><div className="empty-state"><span>⌁</span><b>{performance?.fills ? `${performance.fills} paper fill${performance.fills === 1 ? "" : "s"} recorded` : "No paper fills yet"}</b><small>{positions.length ? `${positions.length} open simulated position${positions.length === 1 ? "" : "s"}; ${performance?.exits ?? 0} closed.` : "All activity is simulated, audited, and never sent to a venue."}</small><small>Closed sample: {performance?.closed_trade_sample ?? 0} · Realized: {money(performance?.realized_pnl)} · Fees: {money(performance?.total_fees)}</small></div></div><div className="panel research-panel"><PanelTitle icon="✦" title="Research signal" subtitle="Intelligence plane" right="NON-ACTIONABLE" /><div className="research-copy"><b>Development strategy only</b><p>No validated profit strategy is active. Research outputs remain advisory and cannot authorize capital.</p><button className="outline-button" onClick={() => setActiveView("Research")}>Open research workspace <span>→</span></button><button className="outline-button" onClick={runPaperCycle} disabled={cycleRunning}>{cycleRunning ? "Running paper scan…" : "Run paper scan"} <span>↗</span></button></div></div></section></>}
      <footer className="footer"><span>PolyTrader · PHASE 8 LIVE READINESS</span><span>LIVE_TRADING_ENABLED = FALSE · DATA SOURCE: POLYMARKET PUBLIC API</span></footer>
    </main></div>;
}

function viewDescription(view: ViewName) {
  return { Overview: "Your Polymarket paper-trading performance and intelligence at a glance.", Markets: "Live public Polymarket markets and the books available to the paper engine.", Opportunities: "Risk-gated opportunities derived from current public market evidence.", Positions: "Open paper positions managed by the execution and accounting layers.", Research: "Advisory research only; signals cannot authorize capital.", System: "Health, data freshness, and fail-closed operating controls." }[view];
}

function WorkspaceView({ view, markets, positions, performance, health, system, cycleRunning, onRunCycle, onOpenResearch }: { view: ViewName; markets: Market[]; positions: Position[]; performance: Performance | null; health: Health | null; system: System | null; cycleRunning: boolean; onRunCycle: () => void; onOpenResearch: () => void }) {
  if (view === "Positions") return <section className="panel markets-panel"><PanelTitle icon="▤" title="Paper positions" subtitle="Managed by the paper engine · no manual orders" right={`${positions.length} OPEN`} /><PositionTable positions={positions} /><div className="research-copy"><small>Paper sells are generated only by the management/risk path; naked selling and live execution are disabled.</small></div></section>;
  if (view === "Research") return <section className="panel research-panel"><PanelTitle icon="✦" title="Research workspace" subtitle="Non-actionable intelligence" right="ADVISORY ONLY" /><div className="research-copy"><b>Learning is evidence-gated</b><p>Signals are recorded for review and cannot bypass RiskManager or authorize live orders.</p><button className="outline-button" onClick={onOpenResearch}>Stay in research <span>↗</span></button></div></section>;
  if (view === "System") return <section className="panel health-panel"><PanelTitle icon="⚙" title="System controls" subtitle="Fail-closed boundaries" right={health?.status === "ok" ? "HEALTHY" : "CHECK CONNECTION"} /><HealthRow label="API" value={health?.status ?? "Waiting"} good={health?.status === "ok"} /><HealthRow label="Trading mode" value={health?.trading_mode ?? "Waiting"} good={health?.trading_mode === "paper"} /><HealthRow label="Live execution" value={system?.live_execution ? "Enabled" : "Disabled"} good={!system?.live_execution} danger={system?.live_execution === true} /><button className="outline-button" onClick={onRunCycle} disabled={cycleRunning}>{cycleRunning ? "Running paper scan…" : "Run paper scan"} <span>↗</span></button></section>;
  return <section className="panel markets-panel"><PanelTitle icon={view === "Markets" ? "◎" : "⌁"} title={view === "Markets" ? "Live Polymarket markets" : "Eligible opportunities"} subtitle="Public data · paper execution only" right={`${markets.length} LOADED`} /><MarketTable markets={markets} /><div className="research-copy"><button className="outline-button" onClick={onRunCycle} disabled={cycleRunning}>{cycleRunning ? "Scanning books…" : "Run paper scan"} <span>↗</span></button><small>{performance?.fills ?? 0} paper fills · {performance?.exits ?? 0} closed trades</small></div></section>;
}

function MarketTable({ markets }: { markets: Market[] }) { return <div className="table-wrap"><table><thead><tr><th>#</th><th>Question</th><th>Status</th><th>Market ID</th><th>Mode</th></tr></thead><tbody>{markets.length ? markets.map((market, index) => <tr key={market.market_id}><td className="muted">{String(index + 1).padStart(2, "0")}</td><td className="question">{market.question || "Unnamed market"}</td><td><span className={`status ${statusLabel(market.status) === "OPEN" ? "open" : ""}`}>{statusLabel(market.status)}</span></td><td className="mono muted">{market.market_id}</td><td><span className="paper-tag">PAPER / READ-ONLY</span></td></tr>) : <tr><td colSpan={5} className="empty">Waiting for public Polymarket data…</td></tr>}</tbody></table></div>; }
function PositionTable({ positions }: { positions: Position[] }) { return <div className="table-wrap"><table><thead><tr><th>Token</th><th>Quantity</th><th>Cost basis</th><th>Mode</th></tr></thead><tbody>{positions.length ? positions.map((position) => <tr key={position.token_id}><td className="mono muted">{position.token_id.slice(0, 18)}…</td><td>{position.quantity}</td><td>{money(position.cost_basis)}</td><td><span className="paper-tag">PAPER</span></td></tr>) : <tr><td colSpan={4} className="empty">No open paper positions.</td></tr>}</tbody></table></div>; }

function Metric({ label, value, note, tone, icon }: { label: string; value: string; note: string; tone: string; icon: string }) { return <article className={`metric ${tone}`}><div className="metric-top"><span>{label}</span><i>{icon}</i></div><strong>{value}</strong><small>{note}</small><div className="meter"><span /></div></article>; }
function PanelTitle({ icon, title, subtitle, right }: { icon: string; title: string; subtitle: string; right: string }) { return <div className="panel-title"><div><span className="panel-icon">{icon}</span><div><h2>{title}</h2><small>{subtitle}</small></div></div><span className="panel-right">{right}</span></div>; }
function HealthRow({ label, value, good, danger = false }: { label: string; value: string; good: boolean; danger?: boolean }) { return <div className="health-row"><span>{label}</span><span>{value}</span><b className={danger ? "danger-text" : good ? "good-text" : "muted"}>▮ {good ? "Healthy" : danger ? "Unsafe" : "Waiting"}</b></div>; }

export default App;
