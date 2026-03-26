import yfinance as yf

class YFinanceAPI:
    # _instance = None

    # def __new__(self, *args,**kwargs):
    #     if not _instance:
    # def __init__(self, stock_list : list[str]):
    #     self.stock_list = stock_list

    def get_history(self,stock_list : list[str],period = '5y') -> list[dict] :
        result = yf.download(stock_list,period=period , group_by = 'Tickers')
        return result.stack(level=0).rename_axis(['Date', 'Ticker']).reset_index(level=1).reset_index().to_dict(orient='records')

    
    def get_stream_data(self, stock_list : list[str], message_handler):
        ws = yf.WebSocket()
        ws.subscribe(symbols=stock_list)
        ws.listen(message_handler)