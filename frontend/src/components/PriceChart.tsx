import { useEffect, useRef } from "react";
import { CandlestickSeries, ColorType, createChart, HistogramSeries, LineSeries } from "lightweight-charts";
import type { Analysis } from "../types";
import { ChartSummary } from "./ChartSummary";

export type ChartRange = 63 | 126 | 252 | "all";

export function PriceChart({ analysis, range }: { analysis: Analysis; range: ChartRange }) {
  const target = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!target.current) return;
    const chart = createChart(target.current, { autoSize: true, height: 470, layout: { background: { type: ColorType.Solid, color: "#101722" }, textColor: "#a8b3c7" }, grid: { vertLines: { color: "#1b2735" }, horzLines: { color: "#1b2735" } }, rightPriceScale: { borderColor: "#263445" }, timeScale: { borderColor: "#263445" } });
    const candles = chart.addSeries(CandlestickSeries, { upColor: "#39c6a3", downColor: "#ef6262", borderVisible: false, wickUpColor: "#39c6a3", wickDownColor: "#ef6262" });
    candles.setData(analysis.bars.map(bar => ({ time: bar.date, open: bar.open, high: bar.high, low: bar.low, close: bar.close })));
    const volume = chart.addSeries(HistogramSeries, { priceFormat: { type: "volume" }, priceScaleId: "", color: "#39526f" });
    volume.priceScale().applyOptions({ scaleMargins: { top: 0.82, bottom: 0 } });
    volume.setData(analysis.bars.map(bar => ({ time: bar.date, value: bar.volume, color: bar.close >= bar.open ? "#277c6d88" : "#b94a4a88" })));
    const smaLines = [
      ["sma_20", "#ffc857", "SMA20"],
      ["sma_50", "#6ea8fe", "SMA50"],
      ["sma_200", "#c990ff", "SMA200"],
    ] as const;
    for (const [field, color, title] of smaLines) {
      const series = chart.addSeries(LineSeries, { color, lineWidth: 1, title });
      series.setData(analysis.indicators.filter(point => point[field] !== null).map(point => ({ time: point.date, value: point[field]! })));
    }
    for (const zone of analysis.zones) candles.createPriceLine({ price: (zone.lower + zone.upper) / 2, color: zone.kind === "support" ? "#39c6a399" : "#e7a94b99", lineWidth: 1, lineStyle: 2, axisLabelVisible: true, title: zone.kind === "support" ? "支撑" : "压力" });
    for (const candidate of analysis.candidates.filter(item => item.status === "valid")) {
      if (candidate.entry) candles.createPriceLine({ price: candidate.entry.center, color: "#6ea8fe", lineWidth: 2, axisLabelVisible: true, title: "加仓" });
      if (candidate.target_one) candles.createPriceLine({ price: candidate.target_one.center, color: "#39c6a3", lineWidth: 1, axisLabelVisible: true, title: "TP1" });
      if (candidate.target_two) candles.createPriceLine({ price: candidate.target_two.center, color: "#39c6a3", lineWidth: 1, axisLabelVisible: true, title: "TP2" });
      if (candidate.invalidation) candles.createPriceLine({ price: candidate.invalidation, color: "#ef6262", lineWidth: 1, axisLabelVisible: true, title: "失效" });
    }
    if (range === "all") chart.timeScale().fitContent();
    else chart.timeScale().setVisibleLogicalRange({ from: Math.max(0, analysis.bars.length - range), to: analysis.bars.length - 1 });
    return () => chart.remove();
  }, [analysis, range]);
  return <section className="chart-shell"><ChartSummary bars={analysis.bars} indicators={analysis.indicators} /><div className="chart" ref={target} aria-label="日线K线图" /></section>;
}
