import type { Analysis } from "./types";

export async function analyze(symbol: string): Promise<Analysis> {
  const response = await fetch(`/api/analysis?symbol=${encodeURIComponent(symbol)}`, { method: "POST" });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail?.message ?? "分析请求失败，请稍后重试。");
  }
  return response.json();
}

export async function getHistory(): Promise<Analysis[]> {
  const response = await fetch("/api/analyses");
  if (!response.ok) throw new Error("无法读取分析历史。");
  return response.json();
}
