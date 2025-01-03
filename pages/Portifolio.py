import boto3
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import io
import base64
from home import download_data_from_s3

# AWS S3 Configurations
S3_BUCKET_NAME = "invest.ia"  # The name of your S3 bucket
S3_REGION = "us-east-1"  # Region where your S3 bucket is located

# Initialize S3 client
s3_client = boto3.client('s3', region_name=S3_REGION)

# Function to load CSS for styling
# Function to load CSS for styling
def load_css():
    st.markdown(
        """
        <style>
        /* General Card Styling */
        .stock-card {
            border: 1px groove #262730;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.5);
            background-color: #262730;
        }
        .stock-title {
            font-size: 20px;
            font-weight: bold;
            color: #00ffcc;
        }
        .stock-subtitle {
            font-size: 14px;
            color: #777;
            margin-bottom: 10px;
        }

        /* Card Type 1 - Two Columns */
        .card-type-1 .grid-container {
            display: grid;
            grid-template-columns: repeat(2, 1fr); /* Two equal columns */
            gap: 10px; /* Space between items */
            text-align: left; /* Align text to the left */
        }
        .card-type-1 .grid-box {
            border: 1px groove #262730;
            padding: 15px;
            background-color: #0E1117;
            color: #fff;
            border-radius: 10px;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )



# Function to display a styled stock card
def display_card_type_1(ticker):
    st.markdown(
        f"""
        <div class="stock-card card-type-1">
            <div class="stock-title">{ticker} - Type 1</div>
            <div class="stock-subtitle">Stock Performance Overview</div>
            <div class="grid-container">
                <div class="grid-box"><strong>Price:</strong><br>$123.45</div>
                <div class="grid-box"><strong>Return:</strong><br>12.34%</div>
                <div class="grid-box"><strong>Volume:</strong><br>1,234,567</div>
                <div class="grid-box"><strong>Market Cap:</strong><br>$100B</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Function to display a styled stock card with an interactive Plotly graph
def display_stock_card(ticker, key_suffix):
    stock_data, metrics_data = download_data_from_s3(ticker, S3_BUCKET_NAME, s3_client)
    stock_data = stock_data.iloc[int(len(stock_data['st'])/2):]
    stock_data["cumsum"] = stock_data['st'].cumsum()
    if stock_data.empty:
        st.error("Could not retrieve data. Please check the ticker symbol.")
        return

    # Create an interactive Plotly graph
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=stock_data.index,
        y=stock_data["cumsum"],
        mode='lines',
        name=f"{ticker} Cumulative Sum",
        line=dict(color='#00ffcc'),
    ))

    fig.update_layout(
        title=f"First Strategy: {ticker}",
        title_font=dict(size=16, color="#ffffff"),
        xaxis=dict(
            showgrid=True,
            gridcolor="#1A1B20",
            gridwidth=0.2,
            zerolinecolor="#f5f5f5",
            zerolinewidth=1,
            color="#ffffff",
            tickfont=dict(color="#00ffcc"),
            title="Date",  # X-axis label
            titlefont=dict(color="#00ffcc")
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#1A1B20",
            gridwidth=0.2,
            zerolinecolor="#f5f5f5",
            zerolinewidth=1,
            color="#ffffff",
            tickfont=dict(color="#00ffcc"),
            title="Cumulative Sum",  # Y-axis label
            titlefont=dict(color="#00ffcc")
        ),
        plot_bgcolor="#262730",
        paper_bgcolor="#262730",
        font=dict(color="#ffcc00"),
        margin=dict(l=15, r=15, t=40, b=15)
    )

    # Display the styled stock card with the interactive Plotly graph
    st.markdown(
        """
        <style>
        .plot-container {
            border-radius: 15px; /* Rounded corners */
            overflow: hidden; /* Ensures the rounded corners show */
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.5);
        }
        .stock-card {
            border: 1px groove #262730;
            border-radius: 10px;
            padding: 15px;
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

    st.markdown(f"""
    <div class="stock-card">
        <div class="stock-title">{ticker}</div>
        <div class="stock-subtitle">Strategy Information - Last 6 Months</div>
        <div class="stock-body">
            <div class="stock-info">
                <p><strong>St Return:</strong> {(stock_data["cumsum"].iloc[-1]) * 100:.2f}%</p>
                <p><strong>Latest Close Price:</strong> ${stock_data['close'].iloc[-1]:.2f}</p>
            </div>
        </div>
        <div class="plot-container">
    """, unsafe_allow_html=True)

    # Embed the interactive Plotly graph
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("</div></div>", unsafe_allow_html=True)

    # Add the button below the card with a unique key but same label
    if st.button("View Strategy", key=f"view_strategy_{key_suffix}"):
        st.session_state['current_ticker'] = ticker  # Store current ticker in session state
        st.session_state['view_full_strategy'] = True  # Flag to indicate we should show the full strategy page

# Function to display details page
def display_details():
    st.title("Stock Details")
    ticker = st.session_state.get('selected_stock', 'Unknown')
    st.write(f"Detailed information for {ticker} will be displayed here.")
    if st.button("Back to Dashboard"):
        st.session_state['current_page'] = 'dashboard'

# Main function to handle navigation
def main():
    if 'current_page' not in st.session_state:
        st.session_state['current_page'] = 'dashboard'

    load_css()

    if st.session_state['current_page'] == 'dashboard':
        st.title("Algorithmic Trading Dashboard")
        st.sidebar.header("Select Stocks")
        stock1 = st.sidebar.selectbox("Select Stock 1", ["BTCUSD"])
        stock2 = st.sidebar.selectbox("Select Stock 2", ["ETHUSD"])
        stock3 = st.sidebar.selectbox("Select Stock 3", ["AAPL"])

        st.header("Stock Performance")
        col1, col2 = st.columns([3, 1])

        with col1:
            display_stock_card(stock1, key_suffix="1")
        with col2:
            display_card_type_1("AAPL")
    elif st.session_state['current_page'] == 'details':
        display_details()

# Run the app
if __name__ == "__main__":
    main()