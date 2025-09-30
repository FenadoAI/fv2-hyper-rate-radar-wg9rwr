import { useEffect, useState } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import axios from "axios";
import { TrendingUp, RefreshCw, Clock, DollarSign, Activity } from "lucide-react";

// BACKEND URL
const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8001';
const API = `${API_BASE}/api`;

// THIS IS WHERE OUR WEBSITE IS HOSTED, [ generate share links relative to this url ]
const MY_HOMEPAGE_URL = API_BASE?.match(/-([a-z0-9]+)\./)?.[1]
  ? `https://${API_BASE?.match(/-([a-z0-9]+)\./)?.[1]}.previewer.live`
  : window.location.origin;

console.log(`MY_HOMEPAGE_URL: ${MY_HOMEPAGE_URL}`);

const Home = () => {
  const [coins, setCoins] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [nextUpdate, setNextUpdate] = useState(null);
  const [error, setError] = useState(null);

  const fetchTopCoins = async (forceRefresh = false) => {
    try {
      setLoading(true);
      setError(null);
      const url = forceRefresh
        ? `${API}/hyperliquid/top-coins?force_refresh=true`
        : `${API}/hyperliquid/top-coins`;
      const response = await axios.get(url);

      if (response.data.success) {
        setCoins(response.data.coins);
        setLastUpdated(new Date(response.data.last_updated));
        setNextUpdate(new Date(response.data.next_update));
      } else {
        setError(response.data.error || 'Failed to fetch data');
      }
    } catch (e) {
      console.error(e);
      setError('Failed to connect to API');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTopCoins();

    // Auto-refresh every minute to check for updates
    const interval = setInterval(() => {
      fetchTopCoins();
    }, 60000);

    return () => clearInterval(interval);
  }, []);

  const formatNumber = (num) => {
    if (num >= 1_000_000_000) {
      return `$${(num / 1_000_000_000).toFixed(2)}B`;
    } else if (num >= 1_000_000) {
      return `$${(num / 1_000_000).toFixed(2)}M`;
    }
    return `$${num.toFixed(2)}`;
  };

  const formatPercentage = (num) => {
    const sign = num >= 0 ? '+' : '';
    return `${sign}${num.toFixed(4)}%`;
  };

  const formatTime = (date) => {
    if (!date) return 'N/A';
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Header */}
      <div className="bg-black/20 backdrop-blur-lg border-b border-white/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="bg-gradient-to-br from-purple-500 to-pink-500 p-3 rounded-xl shadow-lg">
                <TrendingUp className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-white">Hyperliquid Funding Tracker</h1>
                <p className="text-purple-200 text-sm mt-1">Top 10 highest annualized funding rate coins (7-day average)</p>
              </div>
            </div>
            <button
              onClick={() => fetchTopCoins(true)}
              disabled={loading}
              className="bg-purple-500/20 hover:bg-purple-500/30 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-all border border-purple-500/30 disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Bar */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-4 border border-white/20">
            <div className="flex items-center gap-3">
              <Clock className="w-5 h-5 text-purple-300" />
              <div>
                <p className="text-purple-200 text-sm">Last Updated</p>
                <p className="text-white font-semibold">{formatTime(lastUpdated)}</p>
              </div>
            </div>
          </div>
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-4 border border-white/20">
            <div className="flex items-center gap-3">
              <Activity className="w-5 h-5 text-green-300" />
              <div>
                <p className="text-purple-200 text-sm">Next Update</p>
                <p className="text-white font-semibold">{formatTime(nextUpdate)}</p>
              </div>
            </div>
          </div>
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-4 border border-white/20">
            <div className="flex items-center gap-3">
              <DollarSign className="w-5 h-5 text-yellow-300" />
              <div>
                <p className="text-purple-200 text-sm">Filter Criteria</p>
                <p className="text-white font-semibold text-sm">OI &gt; $10M AND Vol &gt; $10M</p>
              </div>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-500/20 border border-red-500/50 text-red-200 px-4 py-3 rounded-lg mb-6">
            <p className="font-semibold">Error: {error}</p>
          </div>
        )}

        {/* Loading State */}
        {loading && coins.length === 0 ? (
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-12 border border-white/20 text-center">
            <RefreshCw className="w-12 h-12 text-purple-300 animate-spin mx-auto mb-4" />
            <p className="text-white text-lg">Loading funding rate data...</p>
            <p className="text-purple-200 text-sm mt-2">This may take a minute as we fetch 7 days of data</p>
          </div>
        ) : (
          /* Data Table */
          <div className="bg-white/10 backdrop-blur-lg rounded-xl border border-white/20 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-black/30">
                  <tr>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-purple-200">Rank</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-purple-200">Coin</th>
                    <th className="px-6 py-4 text-right text-sm font-semibold text-purple-200">Annualized FR (7d)</th>
                    <th className="px-6 py-4 text-right text-sm font-semibold text-purple-200">Current FR</th>
                    <th className="px-6 py-4 text-right text-sm font-semibold text-purple-200">Open Interest</th>
                    <th className="px-6 py-4 text-right text-sm font-semibold text-purple-200">Daily Volume</th>
                    <th className="px-6 py-4 text-right text-sm font-semibold text-purple-200">Data Points</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/10">
                  {coins.map((coin, index) => (
                    <tr
                      key={coin.coin}
                      className="hover:bg-white/5 transition-colors"
                    >
                      <td className="px-6 py-4">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
                          index === 0 ? 'bg-yellow-500 text-black' :
                          index === 1 ? 'bg-gray-400 text-black' :
                          index === 2 ? 'bg-orange-600 text-white' :
                          'bg-purple-500/30 text-purple-200'
                        }`}>
                          {index + 1}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-white font-bold text-lg">{coin.coin}</span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <span className={`font-bold text-lg ${
                          coin.annualized_funding_rate_pct > 0 ? 'text-green-400' : 'text-red-400'
                        }`}>
                          {formatPercentage(coin.annualized_funding_rate_pct)}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <span className={`font-semibold ${
                          coin.current_funding_rate > 0 ? 'text-green-300' : 'text-red-300'
                        }`}>
                          {formatPercentage(coin.current_funding_rate * 100)}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right text-white font-semibold">
                        {formatNumber(coin.open_interest_usd)}
                      </td>
                      <td className="px-6 py-4 text-right text-white font-semibold">
                        {formatNumber(coin.daily_volume_usd)}
                      </td>
                      <td className="px-6 py-4 text-right text-purple-200">
                        {coin.funding_data_points}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Footer Info */}
        <div className="mt-8 bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10">
          <h3 className="text-white font-semibold mb-3">About This Tracker</h3>
          <div className="text-purple-200 text-sm space-y-2">
            <p>• This tracker displays the top 10 cryptocurrencies with the highest annualized funding rates (7-day average) from Hyperliquid perpetual markets.</p>
            <p>• Only coins with Open Interest &gt; $10M AND Daily Volume &gt; $10M are included.</p>
            <p>• Funding rates are annualized (funding occurs every 8 hours, so rate × 3 × 365). Positive rates indicate longs paying shorts.</p>
            <p>• Data updates automatically every hour. You can manually refresh using the button above.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />}>
            <Route index element={<Home />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
