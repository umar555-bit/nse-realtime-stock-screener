from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *

spark = SparkSession.builder \
    .appName("NSE Real-Time Screener") \
    .getOrCreate()

spark.conf.set("spark.sql.shuffle.partitions", "4")
spark.conf.set("spark.default.parallelism", "4")

schema = StructType([
    StructField("symbol", StringType()),
    StructField("price", DoubleType()),
    StructField("volume", IntegerType()),
    StructField("event_time", StringType())
])

df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "172.31.2.62:9092") \
    .option("subscribe", "nifty50_ticks") \
    .option("startingOffsets", "latest") \
    .load()

json_df = df.selectExpr("CAST(value AS STRING)")
parsed_df = json_df.select(
    from_json(col("value"), schema).alias("data")
).select("data.*")

data_df = parsed_df.withColumn(
    "event_time",
    to_timestamp("event_time")
)

agg_df = data_df \
    .withWatermark("event_time", "2 minutes") \
    .groupBy(
        window(col("event_time"), "5 minutes", "1 minute"),
        col("symbol")
    ).agg(
        avg("price").alias("avg_price"),
        avg("volume").alias("avg_volume"),
        max("price").alias("current_price"),
        max("volume").alias("current_volume")
    )

screened_df = agg_df.filter(
    (col("current_price") > col("avg_price") * 1.03) &
    (col("current_volume") > col("avg_volume") * 1.2)
)

query = screened_df.writeStream \
    .outputMode("update") \
    .format("console") \
    .option("truncate", "false") \
    .start()

query.awaitTermination()
