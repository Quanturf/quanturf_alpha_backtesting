import blankly
from time import sleep
import yfinance as yf
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from threading import Thread
from collections import deque
from wallstreet import Stock
import alpaca_trade_api as tradeapi
from blankly.exchanges.exchange import Exchange
from blankly.exchanges.auth.auth_constructor import AuthConstructor
from blankly.exchanges.interfaces.alpaca.alpaca_api import create_alpaca_client
import json

total_stock_price=0.00
qty=0.00
stock=deque()
exch=None
smbl=None

keys_file=open("keys.json","r")
json_data=json.load(keys_file)
strategy_name=""
for x in json_data["alpaca"]:
    strategy_name=x

client=tradeapi.REST(key_id=json_data['alpaca'][strategy_name]['API_KEY'],
                     secret_key=json_data['alpaca'][strategy_name]['API_SECRET'],
                     base_url="https://paper-api.alpaca.markets",
                     api_version='V2')

def portfolio():
    current_price=client.get_latest_trade(smbl).price
    print("stock current price: "+ str(current_price))
    unrealized_profit=float(current_price)*qty-total_stock_price
    print(unrealized_profit)
    # print(s.price*qty)

def live(strategy_name,resolution,init):
    strategy = blankly.Strategy(exch)
    strategy.add_price_event(strategy_name, smbl, resolution=resolution, init=init)
    strategy.start()

def calculate_stock_price():
    global total_stock_price
    total_stock_price=0.00
    for s in stock:
        total_stock_price+=(s[0]*s[1])

def sh_order(order,price):
    order=order.get_response()
    global qty
    global stock
    if order['side'] == "buy":
        stock.append([float(order['size']),price])
        qty+=float(order['size'])
        print("buy qty: "+ str(qty))
        print(stock)
    else:
        qty-=float(order['size'])
        size=float(order['size'])
        print("sell size:"+ str(size))
        print("sell qty: "+ str(qty))
        print('STOCK: '+str(stock))
        if stock[0][0] <= size:
            while stock and stock[0][0] <= size:
                size-=stock[0][0]
                stock.popleft()
            
            if stock:
                stock[0][0]=stock[0][0]-size
        else:
            stock[0][0]=stock[0][0]-size
        print(stock)
    calculate_stock_price()

def cronjob():
    scheduler = BackgroundScheduler()
    scheduler.start()

    trigger = CronTrigger(
        year="*", month="*", day="*", hour="*", minute="*", second="*/5"
    )
    scheduler.add_job(
        portfolio,
        trigger=trigger,
        args=[],
        name="portfolio",
    )
    while True:
        sleep(60)


def run_strategy(exchange,strategy_name,symbol,resolution,init):
    global exch
    global smbl
    exch=exchange
    smbl=symbol 
    t1=Thread(target=live,args=[strategy_name,resolution,init])
    t2=Thread(target=cronjob,args=[])
    t1.start()
    t2.start()
    t1.join()
    t2.join()

