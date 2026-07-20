import type { Candidate } from "../types";

const money = (value: number | null | undefined) => value == null ? "—" : `$${value.toFixed(2)}`;
const label: Record<string, string> = { long_pullback: "多头回踩", long_breakout: "多头突破", short_rejection: "空头反弹失败", short_breakdown: "空头跌破" };

export function StrategyCard({ candidate, primary = false }: { candidate: Candidate; primary?: boolean }) {
  const invalid = candidate.status === "no_opportunity";
  return <article className={`strategy-card ${candidate.direction} ${primary ? "primary" : ""} ${invalid ? "muted" : ""}`}>
    <div className="card-heading"><div><span className="eyebrow">{candidate.direction === "long" ? "LONG" : "SHORT"}</span><h3>{label[candidate.template] ?? candidate.template}</h3></div><strong className="score">{candidate.score.toFixed(0)}<small>/100</small></strong></div>
    {invalid ? <p className="no-opportunity">无有效机会：第一目标的风险收益比不足 1.5R。</p> : <div className="levels">
      <div><span>加仓区</span><b>{money(candidate.entry?.lower)} – {money(candidate.entry?.upper)}</b><small>中心 {money(candidate.entry?.center)}</small></div>
      <div><span>止盈一</span><b>{money(candidate.target_one?.center)}</b><small>{candidate.risk_reward_one?.toFixed(2)}R</small></div>
      <div><span>止盈二</span><b>{money(candidate.target_two?.center)}</b></div>
      <div className="invalidation"><span>失效线</span><b>{money(candidate.invalidation)}</b></div>
    </div>}
    <div className="conditions">{candidate.conditions.map(item => <span key={item}>{item}</span>)}</div>
    {candidate.reason && <p className="reason">{candidate.reason}</p>}
  </article>;
}
