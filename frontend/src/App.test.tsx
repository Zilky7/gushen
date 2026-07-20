import { render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { App } from "./App";

vi.stubGlobal("fetch", vi.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve([]) })));

test("shows an analysis entry state", () => {
  render(<App />);
  expect(screen.getByRole("button", { name: "分析" })).toBeInTheDocument();
  expect(screen.getByText("输入股票，生成日线策略")).toBeInTheDocument();
});
