import type { Analysis } from "../types";

export function HistoryPanel({ items, onOpen }: { items: Analysis[]; onOpen: (item: Analysis) => void }) {
  return <aside className="history"><h2>分析历史</h2>{items.length === 0 ? <p>尚无保存的分析。</p> : items.map(item => <button key={item.id} onClick={() => onOpen(item)}><b>{item.symbol}</b><span>{new Date(item.created_at).toLocaleString()}</span></button>)}</aside>;
}
