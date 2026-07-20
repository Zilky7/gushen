# 股神：美股日线策略研究工具

输入美股代码并点击“分析”，工具会用日线 OHLCV 计算支撑/压力区、趋势、候选加仓区、两级止盈区和失效线。它同时展示多头和空头候选，优先展示多头。

这是一项研究辅助工具，不构成投资建议。它不连接券商、不下单、不自动盯盘，也不会将 LLM 文字当成价格或交易指令。

## 启动

```bash
cp .env.example .env
docker compose up --build
```

打开 `http://localhost:8080`。首版数据源为 yfinance：无需行情 API key；数据可能存在延迟、修订、限流或临时不可用，因此页面会标注缓存数据，无法获取足够数据时不会生成新的价格策略。

本地开发：

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/uvicorn app.main:app --reload

cd ../frontend
npm install
npm run dev
```

## 验证

```bash
cd backend && .venv/bin/pytest -v
cd frontend && npm test -- --run && npm run build
```

## 规则边界

- 日线波段默认面向约 2 天到 3 周持仓。
- 价格来自固定规则：SMA20/50/200、ATR14、20 日均量、三日枢轴和 ATR/百分比聚类的价格区。
- LLM 仅可解释已经计算的结构化事实，任何不在引擎输出中的价格都会被拒绝。
- 策略优化只能读取 2023-01-01 至 2025-12-31；2026-01-01 至 2026-06-30 是隔离的样本外验证期，优化版本不会自动替换基准版本。

## 数据安全

`.env`、SQLite 运行数据、依赖目录和脑暴产物均被 Git 忽略。不要将 API key 提交到版本库或终端输出中。
