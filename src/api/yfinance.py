import asyncio
import json
import logging

import yfinance as yf
from yfinance import AsyncWebSocket

logger = logging.getLogger(__name__)

SYMBOLS_PER_CONNECTION = 50


async def _run_ws(symbols: list[str], conn_id: int, total_conns: int, message_handler):
    while True:
        try:
            ws = AsyncWebSocket(verbose=False)
            await ws._connect()

            if ws._heartbeat_task is not None:
                ws._heartbeat_task.cancel()
                ws._heartbeat_task = None

            ws._subscriptions.update(symbols)
            message = {"subscribe": symbols}
            await ws._ws.send(json.dumps(message))
            logger.info("Connection %d/%d: subscribed %d symbols", conn_id, total_conns, len(symbols))

            async for raw in ws._ws:
                message_json = json.loads(raw)
                encoded_data = message_json.get("message", "")
                decoded = ws._decode_message(encoded_data)
                if message_handler:
                    message_handler(decoded)

        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error("Connection %d/%d error: %s — reconnecting in 5s", conn_id, total_conns, e)
            await asyncio.sleep(5)


class YFinanceAPI:

    def get_history(self, stock_list: list[str], period='5y') -> list[dict]:
        result = yf.download(stock_list, period=period, group_by='Tickers')
        return result.stack(level=0).rename_axis(['Date', 'Ticker']).reset_index(level=1).reset_index().to_dict(orient='records')

    async def get_stream_data(self, stock_list: list[str], message_handler):
        chunks = [
            stock_list[i:i + SYMBOLS_PER_CONNECTION]
            for i in range(0, len(stock_list), SYMBOLS_PER_CONNECTION)
        ]
        total = len(chunks)
        logger.info("Spawning %d WebSocket connections for %d symbols (%d per conn)", total, len(stock_list), SYMBOLS_PER_CONNECTION)

        tasks = [
            asyncio.create_task(_run_ws(chunk, idx + 1, total, message_handler))
            for idx, chunk in enumerate(chunks)
        ]

        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            for t in tasks:
                t.cancel()
            raise