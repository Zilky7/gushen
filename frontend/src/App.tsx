import { FormEvent, useEffect, useState } from "react";
import { analyze, getHistory } from "./api";
import { HistoryPanel } from "./components/HistoryPanel";
import { PriceChart } from "./components/PriceChart";
import { StrategyCard } from "./components/StrategyCard";
import type { Analysis } from "./types";

export function App() {
  const [symbol, setSymbol] = useState("MU");
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [history, setHistory] = useState<Analysis[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => { getHistory().then(setHistory).catch(() => undefined); }, []);
  async function submit(event: FormEvent) { event.preventDefault(); setLoading(true); setError(""); try { const result = await analyze(symbol); setAnalysis(result); setHistory(old => [result, ...old.filter(item => item.id !== result.id)]); } catch (reason) { setError(reason instanceof Error ? reason.message : "分析失败"); } finally { setLoading(false); } }
  const long = analysis?.candidates.filter(item => item.direction === "long") ?? [];
  const short = analysis?.candidates.filter(item => item.direction === "short") ?? [];
  return <main><header><div className="brand">股神 <span>RESEARCH</span></div><div className="disclaimer">日线波段研究 · 不连接券商 · 非投资建议</div></header><div className="layout"><section className="workspace"><form onSubmit={submit}><label htmlFor="symbol">美股代码</label><input id="symbol" value={symbol} onChange={event => setSymbol(event.target.value.toUpperCase())} maxLength={12} /><button disabled={loading}>{loading ? "正在计算…" : "分析"}</button></form>{error && <div className="error" role="alert">{error}</div>}{!analysis && !loading && <section className="empty"><h1>输入股票，生成日线策略</h1><p>系统会计算支撑、压力、加仓区、止盈区和失效线；价格完全由规则引擎计算。</p></section>}{analysis && <><div className="meta"><b>{analysis.symbol}</b><span>{analysis.data_source} · 数据更新：{new Date(analysis.data_updated_at).toLocaleString()}</span>{analysis.stale_cache && <em>使用缓存数据</em>}</div><PriceChart analysis={analysis} /><section className="strategy-grid"><div><h2>多头策略</h2>{long.length ? long.map((item, index) => <StrategyCard key={item.template} candidate={item} primary={index === 0} />) : <p className="empty-card">当前没有符合规则的多头候选。</p>}</div><div><h2>空头候选</h2>{short.length ? short.map(item => <StrategyCard key={item.template} candidate={item} />) : <p className="empty-card">当前没有符合规则的空头候选。</p>}</div></section></>}</section><HistoryPanel items={history} onOpen={setAnalysis} /></div></main>;
}
