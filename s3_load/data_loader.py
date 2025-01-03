import boto3
import pandas as pd
import os
import h5py
import io
from io import BytesIO

class StrategyDataManager:
    def __init__(self, bucket_name, directory, local_temp_dir="/tmp"):
        """
        Initialize the StrategyDataManager.

        :param bucket_name: Name of the S3 bucket.
        :param directory: Directory in the S3 bucket containing the files.
        :param local_temp_dir: Local directory for temporary file storage.
        """
        self.s3 = boto3.client("s3")
        self.bucket_name = bucket_name
        self.directory = directory
        self.local_temp_dir = local_temp_dir

    def list_files(self):
        """
        List all files in the specified S3 directory.

        :return: List of file keys.
        """
        response = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix=self.directory)
        if "Contents" not in response:
            print("No files found in the specified directory.")
            return []
        return [obj["Key"] for obj in response["Contents"] if obj["Key"].endswith(".csv")]

    def download_file(self, s3_key):
        """
        Download a file from S3 to the local temporary directory.

        :param s3_key: Key of the file in S3.
        :return: Local file path.
        """
        file_name = os.path.basename(s3_key)
        local_path = os.path.join(self.local_temp_dir, file_name)
        self.s3.download_file(self.bucket_name, s3_key, local_path)
        print(f"Downloaded {s3_key} to {local_path}")
        return local_path

    def read_csv(self, local_file_path):
        """
        Read a CSV file into a Pandas DataFrame.

        :param local_file_path: Path to the local CSV file.
        :return: Pandas DataFrame.
        """
        df = pd.read_csv(local_file_path)
        print(f"Loaded CSV from {local_file_path}")
        return df

    def save_to_hdf5(self, df, hdf5_file_path, dataset_name):
        """
        Save a DataFrame to an HDF5 file under a specified dataset name.

        :param df: Pandas DataFrame to save.
        :param hdf5_file_path: Path to the HDF5 file.
        :param dataset_name: Dataset name inside the HDF5 file.
        """
        with pd.HDFStore(hdf5_file_path, mode="a") as store:
            store.put(dataset_name, df, format="table", data_columns=True)
        print(f"Saved dataset '{dataset_name}' to {hdf5_file_path}")

    def process_files(self, hdf5_file_path=None):
        """
        Process all CSV files in the S3 directory.

        :param hdf5_file_path: Optional HDF5 file path to save processed data.
        """
        file_keys = self.list_files()
        if not file_keys:
            return

        for s3_key in file_keys:
            # Download and read CSV
            local_file_path = self.download_file(s3_key)
            df = self.read_csv(local_file_path)

            # Optionally save to HDF5
            if hdf5_file_path:
                dataset_name = os.path.splitext(os.path.basename(s3_key))[0]  # Remove .csv extension
                self.save_to_hdf5(df, hdf5_file_path, dataset_name)

            # Clean up local file
            os.remove(local_file_path)
            print(f"Processed and cleaned up {local_file_path}")


# AWS S3 Configurations
S3_BUCKET_NAME = "invest.ia"  # The name of your S3 bucket
S3_REGION = "us-east-1"  # Region where your S3 bucket is located
ticker = 'BTCUSD'

def download_data_from_s3(ticker, S3_BUCKET_NAME, s3_client):
    # Try to get the stock data (HDF5 file) and metrics data (HDF5 file) from the S3 bucket
    try:
        # Construct the S3 keys (paths) for the stock data and metrics data HDF5 files
        stock_s3_key = f"first_strategy/{ticker}_strategy_data.h5"  # e.g., "BTCUSD_strategy_data.h5"
        metrics_s3_key = f"first_strategy/{ticker}_metrics.h5"  # e.g., "BTCUSD_metrics_data.h5"

        # Download the stock data HDF5 from the S3 bucket
        stock_obj = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=stock_s3_key)
        stock_data_buffer = io.BytesIO(stock_obj['Body'].read())

        # Save the buffer to a temporary file
        with open('temp_stock_data.h5', 'wb') as f:
            f.write(stock_data_buffer.getvalue())

        # Read the stock data using h5py
        with h5py.File('temp_stock_data.h5', 'r') as hdf:
            stock_data = pd.DataFrame(hdf['data'][:])  # Adjust the key if necessary

        # Download the metrics data HDF5 from the S3 bucket
        metrics_obj = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=metrics_s3_key)
        metrics_data_buffer = io.BytesIO(metrics_obj['Body'].read())

        # Save the buffer to a temporary file
        with open('temp_metrics_data.h5', 'wb') as f:
            f.write(metrics_data_buffer.getvalue())

        # Read the metrics data using h5py
        with h5py.File('temp_metrics_data.h5', 'r') as hdf:
            metrics_data = pd.DataFrame(hdf['data'][:])  # Adjust the key if necessary

        # Convert the index to a datetime type if necessary (assuming it is in the 'date' column)
        stock_data['date'] = pd.to_datetime(stock_data['date'])
        stock_data.set_index('date', inplace=True)

        # Clean up temporary files
        os.remove('temp_stock_data.h5')
        os.remove('temp_metrics_data.h5')

        # Return both the stock data and metrics data
        return stock_data, metrics_data

    except Exception as e:
        print(f"An error occurred while downloading data from S3: {e}")
        return None, None


s3_client = boto3.client('s3', region_name='us-east-1')
stock_data, metrics_data = download_data_from_s3(ticker, S3_BUCKET_NAME, s3_client)


def load_dataframe_from_s3(bucket_name, file_key, aws_region='us-east-1'):
    """
    Load a Parquet file from S3 into a Pandas DataFrame.

    Args:
    - bucket_name (str): Source S3 bucket name.
    - file_key (str): Source S3 file key (path in the bucket).
    - aws_region (str): AWS region for the S3 bucket.

    Returns:
    - pd.DataFrame: Loaded DataFrame.
    """
    # Create S3 client
    s3_client = boto3.client('s3', region_name=aws_region)

    # Download Parquet file into a buffer
    response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
    parquet_buffer = BytesIO(response['Body'].read())

    # Read the buffer into a Pandas DataFrame
    return pd.read_parquet(parquet_buffer)



# Use the function
bucket_name = "invest.ia"
file_key = 'first_strategy/BTCUSD_strategy_data.parquet'


# Load the DataFrame
df_loaded = load_dataframe_from_s3(bucket_name, file_key)
print(df_loaded)

