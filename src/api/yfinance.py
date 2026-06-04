import asyncio
import json
import logging

import yfinance as yf
from yfinance import AsyncWebSocket

logger = logging.getLogger(__name__)

SUBSCRIBE_BATCH_SIZE = 50
SUBSCRIBE_BATCH_DELAY = 1.0


class YFinanceAPI:

    def get_history(self, stock_list: list[str], period='5y') -> list[dict]:
        result = yf.download(stock_list, period=period, group_by='Tickers')
        return result.stack(level=0).rename_axis(['Date', 'Ticker']).reset_index(level=1).reset_index().to_dict(orient='records')

    async def get_stream_data(self, stock_list: list[str], message_handler):
        ws = AsyncWebSocket()
        await ws._connect()

        ws._subscriptions.update(stock_list)

        total_batches = (len(stock_list) + SUBSCRIBE_BATCH_SIZE - 1) // SUBSCRIBE_BATCH_SIZE
        for i in range(0, len(stock_list), SUBSCRIBE_BATCH_SIZE):
            batch = stock_list[i:i + SUBSCRIBE_BATCH_SIZE]
            message = {"subscribe": batch}
            await ws._ws.send(json.dumps(message))
            logger.info(
                "Subscribed batch %d/%d (%d symbols)",
                i // SUBSCRIBE_BATCH_SIZE + 1,
                total_batches,
                len(batch),
            )
            if i + SUBSCRIBE_BATCH_SIZE < len(stock_list):
                await asyncio.sleep(SUBSCRIBE_BATCH_DELAY)

        logger.info("All %d symbols subscribed in %d batches", len(stock_list), total_batches)
        await ws.listen(message_handler)