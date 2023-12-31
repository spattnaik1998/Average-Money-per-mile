from pyspark.sql import SparkSession
from pyspark.sql.functions import count, desc, udf
from pyspark.sql.types import BooleanType
from pyspark.sql.functions import col
import sys

def is_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False
		
if __name__ == "__main__":
	if len(sys.argv) != 3:
		print("Usage: top_taxis.py <input_file> <output_file>")
		sys.exit(1)
		
	input_file = sys.argv[1]
	output_file = sys.argv[2]
	
	spark = SparkSession.builder.appName("Efficient Drivers").getOrCreate()
	
	is_float_udf = udf(is_float, BooleanType())
	
	df = spark.read.option("header", "false").csv(input_file)
	
	corrected_df = df.filter(is_float_udf("_c5") & is_float_udf("_c11"))
	
	columns = ["medallion", "hack_license", "pickup_datetime", "dropoff_datetime", "trip_time_in_secs",
               "trip_distance", "pickup_longitude", "pickup_latitude", "dropoff_longitude", "dropoff_latitude",
               "payment_type", "fare_amount", "surcharge", "mta_tax", "tip_amount", "tolls_amount", "total_amount"]
			   
	renamed_columns = ["_c0", "_c1", "_c2", "_c3", "_c4", "_c5", "_c6", "_c7", "_c8", "_c9", "_c10", "_c11", "_c12", "_c13", "_c14", "_c15", "_c16"]
	
	for orig_col, new_col in zip(renamed_columns, columns):
		corrected_df = corrected_df.withColumnRenamed(orig_col, new_col)
		
	cleaned_df = corrected_df.dropna()
	
	cleaned_df = cleaned_df.filter(col("medallion").isNotNull() & col("hack_license").isNotNull())
	
	df_with_earned_per_mile = cleaned_df.withColumn("earned_per_mile", col("total_amount") / col("trip_distance"))
	
	average_earned_per_mile = df_with_earned_per_mile.groupBy("hack_license").agg({"earned_per_mile": "avg"}).withColumnRenamed("avg(earned_per_mile)", "avg_earned_per_mile")

	top_efficient_drivers = average_earned_per_mile.orderBy(col("avg_earned_per_mile").desc()).limit(10)
	
	top_efficient_drivers.show()
    
    top_efficient_drivers.write.mode("overwrite").csv(output_file, header=True)
    
    spark.stop()