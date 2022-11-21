import websocket
from datetime import datetime
import requests
import json
import pprint
import numpy
import talib
from binance.client import Client
import csv


config = open("config.json", "r")
configcontent = config.read()
configtoobjects = json.loads(configcontent)

ApiKey = configtoobjects['BinancApiKey']
SecretKey = configtoobjects['BinancSecretKey']
TelegramApitKey = configtoobjects['TelegramApiKey']

#
client = Client(ApiKey, SecretKey)
# client.API_URL = 'https://testnet.binance.vision/api'
#historical_candles = client.get_historical_klines('ETHUSDT',client.KLINE_INTERVAL_1MINUTE, "1 day ago UTC")
#historical_candles = client.get_historical_klines("BTCUSDT", Client.KLINE_INTERVAL_1DAY, "1 Jan, 2017", "1 Jan, 2022")
#historical_candles = client.get_historical_klines("BTCUSDT", Client.KLINE_INTERVAL_5MINUTE, "1 Jan, 2020", "1 Jan, 2022")
#historical_candles = client.get_historical_klines("BTCUSDT", Client.KLINE_INTERVAL_15MINUTE, "1 Jan, 2020", "1 Jan, 2022")
#historical_candles = client.get_historical_klines("BTCUSDT", Client.KLINE_INTERVAL_1MINUTE, "1 Dec, 2020", "1 Jan, 2022")
historical_candles = client.get_historical_klines("BTCUSDT", Client.KLINE_INTERVAL_4HOUR, "1 Dec, 2021", "1 Jan, 2022")
#historical_candles = client.get_historical_klines("BTCUSDT", Client.KLINE_INTERVAL_1HOUR, "1 Jan, 2020", "1 Jan, 2022")


f =open('BTCUSDT-4h-one_year.csv', 'w', newline='')
candlewriter = csv.writer(f, delimiter=',')
#candlewriter.writerow(["Date","Open","High","Low","Close","Adj Close","Volume"])
for candle in historical_candles:
    ts=int(candle[0])
    #time=datetime.utcfromtimestamp(ts/1000).strftime('%Y-%m-%d %H:%M:%S')
    #candlewriter.writerow([time,candle[1],candle[2],candle[3],candle[4],candle[4],candle[5]])
    candle[0]=candle[0]/1000
    candlewriter.writerow(candle)

f.close()
candles = client.get_historical_klines('ETHUSDT',client.KLINE_INTERVAL_1MINUTE, "30 min ago UTC")
closes=[]

for candle in candles:
    #print(candle[4])
    closes.append(float(candle[4]))

socket = "wss://stream.binance.com:9443/ws/ethusdt@kline_1m"

RSI_PERIOD=14
RSI_OVERBOUGHT=65
RSI_OVERSOLD=35
TRADE_SYMBOL='ETHUSDT'
TRADE_QUANTITY=0.05


in_position=False
if len(closes) > RSI_PERIOD:
    np_closes = numpy.array(closes)
    rsi = talib.RSI(np_closes, RSI_PERIOD)
    print("all rsis calculated")
    #print(rsi)
    last_rsi = rsi[-1]
    print("the current rsi is: {}".format(last_rsi))


telegrambotAPI=TelegramApitKey
chat_id="-763358272"

def on_open(ws):
    print("connection opened")


def on_close(ws):
    print("connection closed")


def on_message(ws,message):

    global closes
    print("message received")
    print(message)
    json_message=json.loads(message)

    candle=json_message['k']
    is_candle_closed= candle['x']
    close=candle['c']
    if is_candle_closed:
        print("candle closed at{}".format(close))
        closes.append(float(close))

        print(closes)
        if len(closes)>RSI_PERIOD:
            np_closes = numpy.array(closes)
            rsi = talib.RSI(np_closes,RSI_PERIOD)
            #print("all rsis calculated")
            #print(rsi)
            print("ilość obliczonych rsi:",len(rsi))
            last_rsi=rsi[-1]
            print("the current rsi is: {}".format(last_rsi))

            if last_rsi>RSI_OVERBOUGHT:
                bot_message = "RSI na ETH/USDT:"+str(last_rsi)+" - sprzedawaj"
                sendMessageUrl = "https://api.telegram.org/bot" + telegrambotAPI + \
                                 "/sendMessage?chat_id=" + chat_id + "&text=" + bot_message + "/"
                requests.get(sendMessageUrl)

            if last_rsi < RSI_OVERSOLD:
                bot_message = "RSI na ETH/USDT wynosi:"+str(last_rsi)+" - kupuj"
                sendMessageUrl = "https://api.telegram.org/bot" + telegrambotAPI + \
                                 "/sendMessage?chat_id=" + chat_id + "&text=" + bot_message
                requests.get(sendMessageUrl)

                #binance order logic
ws = websocket.WebSocketApp(socket, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever()
