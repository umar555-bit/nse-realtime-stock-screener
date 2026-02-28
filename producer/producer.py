import yfinance as yf
import json
import time
from kafka import KafkaProducer
from datetime import datetime

symbols = [
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
    "HDFCBANK.NS",
    "ICICIBANK.NS"
]

producer = KafkaProducer(
    bootstrap_servers="172.31.2.62:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

print("Producer Started...")

while True:
    for symbol in symbols:
        try:
            data = yf.download(
                symbol,
                period="1d",
                interval="1m",
                progress=False
            )
            if not data.empty:
                latest = data.iloc[-1]
                message = {
                    "symbol": symbol.replace(".NS", ""),
                    "price": float(latest["Close"]),
                    "volume": int(latest["Volume"]),
                    "event_time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                }
                producer.send("nifty50_ticks", value=message)
                print("Sent:", message)
        except Exception as e:
            print("Error:", e)
    producer.flush()
    time.sleep(60)
