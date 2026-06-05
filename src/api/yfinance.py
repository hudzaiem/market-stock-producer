import asyncio
import json
import logging

import yfinance as yf
from yfinance import AsyncWebSocket

logger = logging.getLogger(__name__)

SUBSCRIBE_BATCH_SIZE = 50
SUBSCRIBE_BATCH_DELAY = 1.0


async def _batched_subscribe(ws, symbols: list[str]):
    total_batches = (len(symbols) + SUBSCRIBE_BATCH_SIZE - 1) // SUBSCRIBE_BATCH_SIZE
    for i in range(0, len(symbols), SUBSCRIBE_BATCH_SIZE):
        batch = symbols[i:i + SUBSCRIBE_BATCH_SIZE]
        message = {"subscribe": batch}
        await ws._ws.send(json.dumps(message))
        logger.info(
            "Subscribed batch %d/%d (%d symbols)",
            i // SUBSCRIBE_BATCH_SIZE + 1,
            total_batches,
            len(batch),
        )
        if i + SUBSCRIBE_BATCH_SIZE < len(symbols):
            await asyncio.sleep(SUBSCRIBE_BATCH_DELAY)
    logger.info("All %d symbols subscribed in %d batches", len(symbols), total_batches)


async def _batched_heartbeat(ws):
    while True:
        try:
            await asyncio.sleep(ws._subscription_interval)
            if ws._subscriptions:
                await _batched_subscribe(ws, list(ws._subscriptions))
                logger.info("Heartbeat: re-subscribed %d symbols in batches", len(ws._subscriptions))
        except Exception as e:
            logger.error("Error in batched heartbeat: %s", e, exc_info=True)
            break


class YFinanceAPI:

    def get_history(self, stock_list: list[str], period='5y') -> list[dict]:
        result = yf.download(stock_list, period=period, group_by='Tickers')
        return result.stack(level=0).rename_axis(['Date', 'Ticker']).reset_index(level=1).reset_index().to_dict(orient='records')

    async def get_stream_data(self, stock_list: list[str], message_handler):
        ws = AsyncWebSocket()
        await ws._connect()

        ws._subscriptions.update(stock_list)

        await _batched_subscribe(ws, stock_list)

        # Override default heartbeat with batched version
        if ws._heartbeat_task is not None:
            ws._heartbeat_task.cancel()
        ws._heartbeat_task = asyncio.create_task(_batched_heartbeat(ws))

        await ws.listen(message_handler)