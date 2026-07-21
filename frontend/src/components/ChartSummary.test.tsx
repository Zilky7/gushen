import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import { ChartSummary } from "./ChartSummary";

test("renders current price change and SMA values", () => {
  render(<ChartSummary bars={[{ date: "2026-07-20", open: 100, high: 103, low: 99, close: 102, volume: 1000 }, { date: "2026-07-21", open: 102, high: 106, low: 101, close: 105, volume: 1200 }]} indicators={[{ date: "2026-07-21", sma_20: 100, sma_50: 95, sma_200: 80 }]} />);
  expect(screen.getByText("$105.00")).toBeInTheDocument();
  expect(screen.getByText("+2.94%")).toBeInTheDocument();
  expect(screen.getByText("SMA 20 100.00")).toBeInTheDocument();
  expect(screen.getByText("SMA 50 95.00")).toBeInTheDocument();
  expect(screen.getByText("SMA 200 80.00")).toBeInTheDocument();
});
