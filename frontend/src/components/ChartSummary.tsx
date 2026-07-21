import type { IndicatorPoint, OhlcvBar } from "../types";

const money = (value: number) => `$${value.toFixed(2)}`;

export function ChartSummary({ bars, indicators }: { bars: OhlcvBar[]; indicators: IndicatorPoint[] }) {
  const latest = bars[bars.length - 1];
  const previous = bars[bars.length - 2];
  const indicator = indicators[indicators.length - 1];
  if (!latest) return null;
  const change = previous ? ((latest.close - previous.close) / previous.close) * 100 : 0;
  const items = [["SMA 20", indicator?.sma_20, "sma20"], ["SMA 50", indicator?.sma_50, "sma50"], ["SMA 200", indicator?.sma_200, "sma200"]] as const;
  return <div className="chart-summary"><div><b>{money(latest.close)}</b><span className={change >= 0 ? "up" : "down"}>{change >= 0 ? "+" : ""}{change.toFixed(2)}%</span><small>{latest.date}</small></div><div className="sma-legend">{items.map(([label, value, style]) => value !== null && value !== undefined && <span className={style} key={label}>{label} {value.toFixed(2)}</span>)}</div></div>;
}
