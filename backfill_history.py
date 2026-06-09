import logging
import os

import clickhouse_connect
import yfinance as yf
from dotenv import load_dotenv

from src.config.stock_list import get_stock_list

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

BATCH_SIZE = 50

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS stock_prices_history (
    ticker String,
    datetime DateTime,
    interval String,
    open Float64,
    high Float64,
    low Float64,
    close Float64,
    volume UInt64
) ENGINE = ReplacingMergeTree()
ORDER BY (ticker, interval, datetime)
"""

PASSES = [
    {"period": "2y", "interval": "60m"},
    {"period": "60d", "interval": "15m"},
]


def get_clickhouse_client():
    return clickhouse_connect.get_client(
        host=os.getenv("CLICKHOUSE_HOST", "localhost"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
        username=os.getenv("CLICKHOUSE_USER", "default"),
        password=os.getenv("CLICKHOUSE_PASSWORD", ""),
        secure=os.getenv("CLICKHOUSE_SECURE", "false").lower() == "true",
        verify=os.getenv("CLICKHOUSE_VERIFY", "false").lower() == "true",
    )


def download_and_insert(client, stock_list, period, interval):
    total_batches = (len(stock_list) + BATCH_SIZE - 1) // BATCH_SIZE
    total_rows = 0

    for batch_idx in range(0, len(stock_list), BATCH_SIZE):
        batch = stock_list[batch_idx:batch_idx + BATCH_SIZE]
        batch_num = batch_idx // BATCH_SIZE + 1

        try:
            df = yf.download(batch, period=period, interval=interval, group_by="Tickers")
            if df.empty:
                logger.warning("Batch %d/%d: empty result, skipping", batch_num, total_batches)
                continue

            stacked = (
                df.stack(level=0)
                .rename_axis(["Datetime", "Ticker"])
                .reset_index()
            )

            stacked["Datetime"] = stacked["Datetime"].dt.tz_localize(None)

            rows = [
                (
                    row["Ticker"],
                    row["Datetime"].to_pydatetime(),
                    interval,
                    float(row["Open"]),
                    float(row["High"]),
                    float(row["Low"]),
                    float(row["Close"]),
                    int(row["Volume"]),
                )
                for _, row in stacked.iterrows()
                if row["Volume"] > 0
            ]

            if rows:
                client.insert(
                    "stock_prices_history",
                    rows,
                    column_names=["ticker", "datetime", "interval", "open", "high", "low", "close", "volume"],
                )

            total_rows += len(rows)
            logger.info(
                "Batch %d/%d [%s %s]: inserted %d rows (total: %d)",
                batch_num, total_batches, interval, period, len(rows), total_rows,
            )

        except Exception as e:
            logger.error("Batch %d/%d [%s %s] failed: %s", batch_num, total_batches, interval, period, e)

    return total_rows


def main():
    client = get_clickhouse_client()
    client.command(CREATE_TABLE_SQL)
    logger.info("Table stock_prices_history ready")

    stock_list = get_stock_list()
    logger.info("Loaded %d stocks", len(stock_list))

    for pass_cfg in PASSES:
        period = pass_cfg["period"]
        interval = pass_cfg["interval"]
        logger.info("=== Starting pass: %s / %s ===", interval, period)
        total = download_and_insert(client, stock_list, period, interval)
        logger.info("=== Finished pass: %s / %s — %d rows total ===", interval, period, total)

    client.close()
    logger.info("Backfill complete")


if __name__ == "__main__":
    main()
