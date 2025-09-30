# FENADO Worklog

## 2025-09-30 - Update: Annualized Funding Rate & Volume Filter

### Changes Made:
1. **Annualized Funding Rate Display:**
   - Changed funding rate display from per-period to annualized format
   - Formula: annualized_rate = avg_rate × 3 × 365 (funding occurs every 8 hours)
   - Updated backend to calculate and return `annualized_funding_rate` and `annualized_funding_rate_pct`
   - Updated frontend to display annualized rates in main table
   - Sorting now based on annualized rate (highest first)

2. **Volume Filter Update:**
   - Changed filter logic from OR to AND condition
   - Old: OI > $10M OR Daily Volume > $100M
   - New: OI > $10M AND Daily Volume > $10M
   - This ensures only coins with significant volume (>$10M daily) are shown
   - Removes low-volume coins from the tracker

3. **Files Modified:**
   - `backend/hyperliquid_service.py`: Added annualization logic, updated filter condition
   - `backend/server.py`: Added annualized fields to HyperliquidCoin model
   - `frontend/src/App.js`: Updated display to show annualized rates, updated filter text

4. **Services Restarted:**
   - Backend rebuilt and restarted successfully
   - Frontend built and restarted successfully
   - All services operational

---

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
