# FENADO Worklog

## 2025-09-30 - Hyperliquid Funding Rate Tracker

### Task: Build website showing top 10 highest average funding rate coins
- Requirements:
  - Show coins with highest avg funding rate (last 7 days)
  - Filter: OI > $10M OR daily volume > $100M
  - Update every hour via Hyperliquid public API
  - Single-page, read-only display

### Implementation Completed ✅

**Backend:**
- Created `hyperliquid_service.py` with HyperliquidService class
- Fetches data from Hyperliquid public API (api.hyperliquid.xyz)
- Calculates 7-day average funding rates for all perpetual markets
- Filters coins by: open_interest > $10M OR daily_volume > $100M
- Returns top 10 coins sorted by average funding rate
- Added API endpoint: `GET /api/hyperliquid/top-coins`
- Implemented MongoDB caching (collection: hyperliquid_top_coins)
- Added APScheduler for hourly automated updates
- Fixed timezone handling for datetime objects

**Frontend:**
- Beautiful gradient design (slate-900 to purple-900)
- Displays top 10 coins in responsive table format
- Shows: Rank, Coin, Avg Funding Rate (7d), Current FR, OI, Volume, Data Points
- Auto-refresh every minute to check for updates
- Manual refresh button with loading states
- Stats cards showing: Last Updated, Next Update, Filter Criteria
- Color-coded ranks (gold, silver, bronze medals)
- Green/red colors for positive/negative funding rates
- Informational footer explaining the tracker

**Technical Details:**
- Backend uses aiohttp for async API calls
- Processes 60+ perpetual markets
- Fetches 168 data points (7 days × 24 hours) per coin
- APScheduler runs update job every hour
- Frontend auto-refreshes display every 60 seconds
- Responsive design with Tailwind CSS and Lucide icons

**Testing:**
- Successfully tested with real Hyperliquid data
- Top coins include: STBL (0.0143%), ASTER (0.0078%), XPL (0.0058%)
- API response time: ~13 seconds for full data fetch
- All services running and operational
