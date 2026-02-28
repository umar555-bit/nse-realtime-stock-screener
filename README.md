# Real-Time Nifty 50 Stock Screener

A production-style real-time stock screening pipeline built on Apache Kafka,
Apache Spark Structured Streaming, and AWS EC2. The system continuously monitors
Nifty 50 stocks and surfaces momentum breakout signals using rolling price and
volume analysis.

---

## Architecture

```
Yahoo Finance API --> Python Producer --> Kafka Topic --> Spark Structured Streaming --> Screened Output
```

The pipeline runs across two dedicated EC2 instances:

- **Kafka EC2**: Hosts the Kafka broker and runs the Python producer that fetches
  1-minute candle data from Yahoo Finance and publishes it to the `nifty50_ticks` topic.

- **Spark EC2**: Runs the Spark Structured Streaming job that consumes from Kafka,
  performs stateful windowed aggregation, and applies the screening logic.

---

## Data Flow

1. The Python producer polls Yahoo Finance every 60 seconds for the latest 1-minute
   candle for each tracked Nifty 50 symbol.
2. Each tick is serialized as JSON and published to the Kafka topic `nifty50_ticks`.
3. Kafka buffers the stream and decouples the producer from the processing layer.
4. Spark reads the live stream from Kafka using event-time windowing to compute
   rolling aggregates per stock.
5. Stocks satisfying both screening conditions are written to the output sink.

---

## Screening Logic

A 5-minute rolling window (sliding every 1 minute) is maintained per stock symbol.
Within each window, the following metrics are computed:

| Metric           | Description                          |
|------------------|--------------------------------------|
| `avg_price`      | 5-minute average closing price       |
| `avg_volume`     | 5-minute average volume              |
| `current_price`  | Latest closing price in the window   |
| `current_volume` | Latest volume in the window          |

A stock is flagged only when both conditions are satisfied simultaneously:

```
current_price  > avg_price  * 1.03   # 3% short-term price breakout
current_volume > avg_volume * 1.20   # 20% volume spike confirmation
```

This combination filters for stocks exhibiting genuine momentum rather than
price movement unsupported by volume.

---

## Stream Processing Configuration

| Parameter         | Value      |
|-------------------|------------|
| Window Duration   | 5 minutes  |
| Slide Interval    | 1 minute   |
| Watermark         | 2 minutes  |
| Output Mode       | Update     |
| Shuffle Partitions| 4          |

The watermark of 2 minutes bounds the state store size, preventing unbounded
memory growth during long-running jobs. Shuffle partitions are tuned to 4 to
match the available cores on the small EC2 instance.

---

## Technologies

| Layer              | Technology                        |
|--------------------|-----------------------------------|
| Market Data Source | Yahoo Finance (yfinance)          |
| Message Broker     | Apache Kafka                      |
| Stream Processor   | Apache Spark 3.5 Structured Streaming |
| Cloud Infrastructure | AWS EC2 (2 instances)           |
| Language           | Python                            |
| Serialization      | JSON                              |

---

## Key Engineering Concepts Demonstrated

- Real-time stream ingestion with Apache Kafka
- Stateful stream processing with event-time semantics
- Sliding window aggregations over live data
- Watermark-based late data handling and state cleanup
- Decoupled producer-consumer architecture
- Cloud deployment and configuration on AWS EC2
- Resource-aware Spark tuning for constrained environments

---

## Planned Improvements

- Replace simple average with Exponential Moving Average (EMA) for more
  responsive signal generation
- Implement VWAP (Volume Weighted Average Price) as an additional filter
- Persist screened stocks to a time-series database such as PostgreSQL or Cassandra
- Build a Streamlit dashboard for real-time visualization of screened signals
- Scale the pipeline to cover the full Nifty 50 universe on a larger cluster
- Integrate an alerting layer via Telegram or Email for immediate notifications
