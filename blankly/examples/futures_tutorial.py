import blankly
from blankly import futures, Side
from blankly.futures import FuturesStrategyState
from blankly.futures.utils import close_position


def price_event(price, symbol, state: FuturesStrategyState):
    prev_price = state.variables['prev_price']
    position = state.interface.get_position(symbol)

    # if the price rose more than 1,000 and we don't already have a short position, then short sell
    if not position and price - prev_price >= 1000:
        order_size = (state.interface.cash / price) * 0.99
        state.interface.market_order(symbol, Side.SELL, order_size)

    # if the price stablized and we *do* have a short position, close our position.
    elif position and abs(price - prev_price) <= 100:
        # we use abs(position['size']) here because position['size'] can (and will) be negative, since we have taken a short position.
        state.interface.market_order(symbol, Side.BUY, abs(position['size']), reduce_only=True)

    state.variables['prev_price'] = price


# This function will be run before our algorithm starts
def init(symbol, state: FuturesStrategyState):
    # Close any open positions
    close_position(symbol, state)

    # Give the algo the previous price as context
    last_price = state.interface.history(symbol, to=1, return_as='deque', resolution=state.resolution)['close'][-1]
    state.variables['prev_price'] = last_price


if __name__ == "__main__":
    exchange = futures.BinanceFutures()
    strategy = futures.FuturesStrategy(exchange)

    strategy.add_price_event(price_event, init=init, teardown=close_position, symbol='BTC-USDT', resolution='1d')

    if blankly.is_deployed:
        strategy.start()
    else:
        strategy.backtest(to='1y', initial_values={'USDT': 10000})
