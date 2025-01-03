import boto3
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import io
import base64
from io import BytesIO

# AWS S3 Configurations
S3_BUCKET_NAME = "invest.ia"  # The name of your S3 bucket
S3_REGION = "us-east-1"  # Region where your S3 bucket is located

# Initialize S3 client
s3_client = boto3.client('s3', region_name=S3_REGION)


# Function to load CSS for styling
def load_css():
    with open("theme/assets/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# Function to download stock and metrics data from S3
#@st.cache_data
def load_dataframe_from_s3(bucket_name, file_key,_s3_client, aws_region='us-east-1'):
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
    response = _s3_client.get_object(Bucket=bucket_name, Key=file_key)
    parquet_buffer = BytesIO(response['Body'].read())

    # Read the buffer into a Pandas DataFrame
    return pd.read_parquet(parquet_buffer)


@st.cache_data
def download_data_from_s3(ticker, S3_BUCKET_NAME, _s3_client):
    # Construct the S3 keys (paths) for the stock data and metrics data CSV files
    stock_s3_key = f"first_strategy/{ticker}_strategy_data.parquet"  # e.g., "AAPL_strategy_data.parquet"
    metrics_s3_key = f"first_strategy/{ticker}_metrics.parquet"  # e.g., "AAPL_metrics.parquet"

    try:
        # Download stock data from S3
        stock_data = load_dataframe_from_s3(S3_BUCKET_NAME, stock_s3_key,_s3_client)

        # Download metrics data from S3
        metrics_data = load_dataframe_from_s3(S3_BUCKET_NAME, metrics_s3_key,_s3_client)

        # Ensure 'date' column exists and process it
        if 'date' in stock_data.columns:
            stock_data['date'] = pd.to_datetime(stock_data['date'])
            stock_data.set_index('date', inplace=True)
        else:
            st.warning(f"Missing 'date' column in stock data for {ticker}.")

        return stock_data, metrics_data

    except Exception as e:
        st.error(f"Error retrieving data for {ticker}: {str(e)}")
        return pd.DataFrame(), pd.DataFrame()  # Return empty DataFrames if the data could not be fetched


# Function to create and return a base64-encoded plot of stock data
def generate_plot_base64(stock_data, ticker):
    # cumsum = stock_data['st'].cumsum()
    # Create the plot with Plotly
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=stock_data.index,
        y=stock_data["cumsum"],
        mode='lines',
        name=f"{ticker} Closing Prices",
        line=dict(color='#00ffcc'),
    ))

    fig.update_layout(
        title_font=dict(size=20, color="#ffffff"),
        xaxis=dict(
            showgrid=False,
            gridcolor="#f5f5f5",
            zerolinecolor="#f5f5f5",
            color="#ffffff",
            tickfont=dict(color="#262730"),
            titlefont=dict(color="#262730")
        ),
        yaxis=dict(
            showgrid=False,
            gridcolor="#f5f5f5",
            zerolinecolor="#f5f5f5",
            color="#ffffff",
            tickfont=dict(color="#262730"),
            titlefont=dict(color="#262730")
        ),
        plot_bgcolor="#262730",
        paper_bgcolor="#262730",
        font=dict(color="#ffcc00"),
        template="plotly",
        margin=dict(l=10, r=10, t=40, b=10)
    )

    # Convert Plotly figure to an image and encode as base64
    img_bytes = fig.to_image(format="png", width=700, height=400, scale=2)
    base64_image = base64.b64encode(img_bytes).decode('utf-8')
    return base64_image


# Function to display a styled stock card
def display_stock_card(ticker, key_suffix):
    stock_data, metrics_data = download_data_from_s3(ticker, S3_BUCKET_NAME, s3_client)
    stock_data = stock_data.iloc[int(len(stock_data['st'])/2):]
    stock_data["cumsum"] = stock_data['st'].cumsum()
    if stock_data.empty:
        st.error("Could not retrieve data. Please check the ticker symbol.")
        return

    # Generate base64 plot
    plot_base64 = generate_plot_base64(stock_data, ticker)

    # Create a styled container for the stock card
    st.markdown(
        """
        <style>
        .stock-card {
            border: 1px groove #262730;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.5);
            background-color: #262730;
            text-align: center;
        }
        .stock-title {
            font-size: 20px;
            font-weight: bold;
            color:  #00ffcc;
        }
        .stock-subtitle {
            font-size: 14px;
            color: #777;
            margin-bottom: 10px;
        }
        .stock-body {
            margin: 10px 0;
        }
        .stock-info {
            display: flex;
            justify-content: space-between;  /* To ensure space between items */
            align-items: center;  /* Center the items vertically */
            margin: 10px 0;
        }
        .stock-info p {
            margin: 0 15px;  /* Add space between the paragraphs */
        }
        .stock-plot {
            margin-top: 15px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Display the card with stock information and plot
    st.markdown(f"""
    <div class="stock-card">
        <div class="stock-title">{ticker}</div>
        <div class="stock-subtitle">Strategy Information - Last 6 Months</div>
        <div class="stock-body">
            <div class="stock-info">
                <p><strong>St Return:</strong> {( stock_data["cumsum"].iloc[-1]) * 100:.2f}%</p>
                <p><strong>Latest Close Price:</strong> ${stock_data['close'].iloc[-1]:.2f}</p>
            </div>
        </div>
        <div class="stock-plot">
            <img src="data:image/png;base64,{plot_base64}" alt="Stock Plot" />
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Add the button below the card with a unique key but same label
    if st.button("View Strategy", key=f"view_strategy_{key_suffix}"):
        st.session_state['current_ticker'] = ticker  # Store current ticker in session state
        st.session_state['view_full_strategy'] = True  # Flag to indicate we should show the full strategy page


# Function to display full strategy details
def display_full_strategy():
    ticker = st.session_state.get('current_ticker')
    if not ticker:
        st.error("No ticker selected for strategy view.")
        return

    stock_data, metrics_data = download_data_from_s3(ticker, S3_BUCKET_NAME, s3_client)

    if stock_data.empty or metrics_data.empty:
        st.error("Could not retrieve full strategy data.")
        return

    st.header(f"Full Strategy for {ticker}")

    # Display more detailed metrics and data
    st.write("### Stock Data:")
    st.write(stock_data.tail())

    st.write("### Metrics Data:")
    st.write(metrics_data.tail())

    # Add more detailed information about the strategy
    st.write("### Strategy Performance Metrics")
    st.write(metrics_data.describe())


# Streamlit app
st.title("Stock Dashboard")


# Main function
def main():
    load_css()
    st.title("Algorithmic Trading Dashboard")

    st.sidebar.header("Select Stocks")
    stock1 = st.sidebar.selectbox("Select Stock 1", ["BTCUSD"])
    stock2 = st.sidebar.selectbox("Select Stock 2", ["BTCUSD"])
    stock3 = st.sidebar.selectbox("Select Stock 3", ["BTCUSD"])

    # Display stock cards
    st.header("Stock Performance")
    col1, col2, col3 = st.columns(3)

    with col1:
        display_stock_card(stock1, key_suffix="1")

    with col2:
        display_stock_card(stock2, key_suffix="2")

    with col3:
        display_stock_card(stock3, key_suffix="3")


if __name__ == "__main__":
    main()