# Hyperliquid Funding Rate Tracker - Implementation Plan

## Requirement ID: e1890a16-ff05-4346-a5b0-760978982274

## Objective
Build a website displaying top 10 coins with highest average funding rate (7-day) from Hyperliquid perpetual market, filtered by OI > $10M OR daily volume > $100M.

## Technical Approach

### 1. Backend API Development
- **Endpoint**: `GET /api/hyperliquid/top-coins`
- **Data Source**: Hyperliquid public API
- **Processing Logic**:
  - Fetch all perpetual markets
  - Get funding rate history (last 7 days)
  - Calculate average funding rate per coin
  - Filter by: open_interest > $10M OR daily_volume > $100M
  - Sort by average funding rate (descending)
  - Return top 10

### 2. Data Caching Strategy
- Store results in MongoDB collection: `hyperliquid_top_coins`
- Fields: `{coins: [], last_updated: DateTime, next_update: DateTime}`
- Update frequency: Every 1 hour
- Background job using Python scheduler

### 3. Frontend Display
- Single-page React application
- Display table with columns:
  - Rank
  - Coin Symbol
  - Average Funding Rate (7-day)
  - Open Interest (USD)
  - Daily Volume (USD)
  - Last Updated timestamp
- Auto-refresh display every minute
- Responsive design with Tailwind CSS

### 4. Automation
- APScheduler for hourly data refresh
- Run on backend startup
- Error handling and retry logic

## Success Criteria
- [x] API successfully connects to Hyperliquid
- [ ] Correct calculation of 7-day average funding rate
- [ ] Accurate filtering by OI/volume thresholds
- [ ] Hourly automated updates
- [ ] Clean, responsive UI displaying top 10 coins
- [ ] Last updated timestamp visible

## Development Steps
1. Research Hyperliquid API documentation
2. Create backend endpoint with data fetching logic
3. Implement MongoDB caching
4. Add scheduler for hourly updates
5. Build frontend table component
6. Test with real data
7. Deploy and monitor
