export type Direction = "long" | "short";
export type OpportunityStatus = "valid" | "no_opportunity";
export interface OhlcvBar { date: string; open: number; high: number; low: number; close: number; volume: number; }
export interface IndicatorPoint { date: string; sma_20: number | null; sma_50: number | null; sma_200: number | null; }
export interface PriceRange { lower: number; center: number; upper: number; source: string; }
export interface PriceZone { kind: string; lower: number; upper: number; strength: number; touches: number; pivot_dates: string[]; }
export interface Candidate { template: string; direction: Direction; status: OpportunityStatus; score: number; entry: PriceRange | null; target_one: PriceRange | null; target_two: PriceRange | null; invalidation: number | null; risk_reward_one: number | null; conditions: string[]; reason?: string | null; risks: string[]; triggers: string[]; }
export interface Analysis { id: string; symbol: string; created_at: string; data_updated_at: string; data_source: string; stale_cache: boolean; strategy_version: string; bars: OhlcvBar[]; indicators: IndicatorPoint[]; zones: PriceZone[]; candidates: Candidate[]; }
