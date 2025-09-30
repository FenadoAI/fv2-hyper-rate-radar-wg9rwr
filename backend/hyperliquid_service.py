"""Service for fetching and processing Hyperliquid perpetual market data."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)

HYPERLIQUID_API_URL = "https://api.hyperliquid.xyz/info"


class HyperliquidService:
    """Service to fetch and process Hyperliquid data."""

    def __init__(self):
        self.api_url = HYPERLIQUID_API_URL

    async def fetch_meta_and_contexts(self) -> tuple[List[Dict], List[Dict]]:
        """Fetch perpetual markets metadata and current contexts."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.api_url,
                json={"type": "metaAndAssetCtxs"},
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status != 200:
                    raise Exception(f"API request failed: {response.status}")
                data = await response.json()
                universe = data[0]["universe"]
                contexts = data[1]
                return universe, contexts

    async def fetch_funding_history(
        self, coin: str, start_time: int, end_time: Optional[int] = None
    ) -> List[Dict]:
        """Fetch historical funding rates for a coin."""
        payload = {
            "type": "fundingHistory",
            "coin": coin,
            "startTime": start_time,
        }
        if end_time:
            payload["endTime"] = end_time

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.api_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status != 200:
                    logger.warning(f"Failed to fetch funding history for {coin}: {response.status}")
                    return []
                return await response.json()

    def calculate_average_funding_rate(self, funding_history: List[Dict]) -> float:
        """Calculate average funding rate from history."""
        if not funding_history:
            return 0.0

        rates = [float(entry["fundingRate"]) for entry in funding_history]
        return sum(rates) / len(rates) if rates else 0.0

    async def get_top_funding_rate_coins(
        self,
        min_open_interest: float = 10_000_000,
        min_daily_volume: float = 10_000_000,
        days_back: int = 7,
        top_n: int = 10,
    ) -> List[Dict]:
        """
        Get top N coins with highest average funding rate (annualized).

        Args:
            min_open_interest: Minimum open interest in USD (default 10M)
            min_daily_volume: Minimum daily volume in USD (default 10M)
            days_back: Number of days to look back for funding rate (default 7)
            top_n: Number of top coins to return (default 10)

        Returns:
            List of coin data sorted by annualized funding rate
        """
        logger.info("Fetching Hyperliquid market data...")

        # Fetch current market data
        universe, contexts = await self.fetch_meta_and_contexts()

        # Calculate time range for funding history
        end_time = int(datetime.now(timezone.utc).timestamp() * 1000)
        start_time = int((datetime.now(timezone.utc) - timedelta(days=days_back)).timestamp() * 1000)

        eligible_coins = []

        for i, coin_meta in enumerate(universe):
            if i >= len(contexts):
                continue

            coin_name = coin_meta["name"]
            context = contexts[i]

            # Parse market data
            try:
                open_interest_str = context.get("openInterest", "0")
                mark_price_str = context.get("markPx", "0")
                daily_volume_str = context.get("dayNtlVlm", "0")

                # Convert to float
                open_interest = float(open_interest_str)
                mark_price = float(mark_price_str)
                daily_volume = float(daily_volume_str)

                # Calculate USD values
                open_interest_usd = open_interest * mark_price
                daily_volume_usd = daily_volume

                # Apply filters: OI > 10M AND daily volume > 10M
                if open_interest_usd < min_open_interest or daily_volume_usd < min_daily_volume:
                    logger.debug(
                        f"Skipping {coin_name}: OI=${open_interest_usd:,.0f}, Vol=${daily_volume_usd:,.0f}"
                    )
                    continue

                logger.info(
                    f"Fetching funding history for {coin_name} (OI=${open_interest_usd:,.0f}, Vol=${daily_volume_usd:,.0f})"
                )

                # Fetch funding history
                funding_history = await self.fetch_funding_history(coin_name, start_time, end_time)

                if not funding_history:
                    logger.warning(f"No funding history for {coin_name}")
                    continue

                # Calculate average funding rate
                avg_funding_rate = self.calculate_average_funding_rate(funding_history)

                # Annualize funding rate: Hyperliquid charges funding every 8 hours (3 times per day)
                # So annualized rate = avg_rate * 3 * 365
                annualized_funding_rate = avg_funding_rate * 3 * 365
                annualized_funding_rate_pct = annualized_funding_rate * 100

                # Current funding rate (annualized)
                current_funding_rate = float(context.get("funding", "0"))
                current_funding_rate_annualized = current_funding_rate * 3 * 365
                current_funding_rate_annualized_pct = current_funding_rate_annualized * 100

                # Total funding earned in last 7 days (sum of all funding rates)
                total_7d_funding = sum(float(entry["fundingRate"]) for entry in funding_history)
                total_7d_funding_pct = total_7d_funding * 100

                eligible_coins.append({
                    "coin": coin_name,
                    "avg_funding_rate": avg_funding_rate,
                    "avg_funding_rate_pct": avg_funding_rate * 100,  # Per-period percentage
                    "annualized_funding_rate": annualized_funding_rate,
                    "annualized_funding_rate_pct": annualized_funding_rate_pct,
                    "current_funding_rate": current_funding_rate,
                    "current_funding_rate_annualized": current_funding_rate_annualized,
                    "current_funding_rate_annualized_pct": current_funding_rate_annualized_pct,
                    "total_7d_funding_pct": total_7d_funding_pct,
                    "open_interest_usd": open_interest_usd,
                    "daily_volume_usd": daily_volume_usd,
                    "mark_price": mark_price,
                    "funding_data_points": len(funding_history),
                })

                logger.info(
                    f"{coin_name}: Avg Funding Rate = {avg_funding_rate * 100:.4f}% | Annualized = {annualized_funding_rate_pct:.2f}% ({len(funding_history)} data points)"
                )

            except (ValueError, KeyError, TypeError) as e:
                logger.error(f"Error processing {coin_name}: {e}")
                continue

        # Sort by annualized funding rate (highest first)
        eligible_coins.sort(key=lambda x: x["annualized_funding_rate"], reverse=True)

        # Return top N
        top_coins = eligible_coins[:top_n]

        logger.info(f"Returning top {len(top_coins)} coins by funding rate")
        return top_coins
