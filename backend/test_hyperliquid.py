"""Test script for Hyperliquid API functionality."""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from hyperliquid_service import HyperliquidService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


async def test_hyperliquid_service():
    """Test Hyperliquid service."""
    print("=" * 80)
    print("Testing Hyperliquid Service")
    print("=" * 80)

    service = HyperliquidService()

    # Test fetching top coins
    print("\n📊 Fetching top 10 coins with highest funding rates...")
    print("-" * 80)

    try:
        coins = await service.get_top_funding_rate_coins()

        print(f"\n✅ Successfully fetched {len(coins)} coins\n")

        print(f"{'Rank':<6}{'Coin':<10}{'Avg FR %':<15}{'Current FR %':<15}{'OI (USD)':<20}{'Volume (USD)':<20}")
        print("-" * 100)

        for i, coin in enumerate(coins, 1):
            print(
                f"{i:<6}{coin['coin']:<10}{coin['avg_funding_rate_pct']:<15.6f}{coin['current_funding_rate'] * 100:<15.6f}"
                f"${coin['open_interest_usd']:>18,.0f}  ${coin['daily_volume_usd']:>18,.0f}"
            )

        print("-" * 100)
        print(f"\n🎯 Test completed successfully!")
        return True

    except Exception as exc:
        print(f"\n❌ Error: {exc}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_hyperliquid_service())
    sys.exit(0 if success else 1)
