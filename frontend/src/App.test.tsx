import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import { App } from "./App";

vi.mock("./components/PriceChart", () => ({ PriceChart: () => <div data-testid="price-chart" /> }));
vi.stubGlobal("fetch", vi.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve([]) })));
afterEach(() => cleanup());

test("shows an analysis entry state", () => {
  render(<App />);
  expect(screen.getByRole("button", { name: "分析" })).toBeInTheDocument();
  expect(screen.getByText("输入股票，生成日线策略")).toBeInTheDocument();
});

test("shows chart period controls after an analysis", async () => {
  vi.mocked(fetch).mockResolvedValueOnce({ ok: true, json: () => Promise.resolve([]) } as Response)
    .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({ id: "1", symbol: "MU", created_at: "2026-07-21T00:00:00Z", data_updated_at: "2026-07-21T00:00:00Z", data_source: "nasdaq", stale_cache: false, strategy_version: "baseline", bars: [], indicators: [], zones: [], candidates: [] }) } as Response);
  render(<App />);

  fireEvent.click(screen.getByRole("button", { name: "分析" }));

  expect(await screen.findByRole("button", { name: "6个月" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "3个月" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "1年" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "全部" })).toBeInTheDocument();
});
