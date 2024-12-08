import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import io
import base64

st.set_page_config(layout="wide")

# Load CSS
def load_css():
    with open("theme/assets/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# Function to download stock data
def download_stock_data(ticker):
    stock_data = yf.download(ticker, period="1mo", interval="1d")
    return stock_data


# Function to plot stock data
# Function to create a plot and return it as a base64-encoded string
def generate_plot_base64(stock_data, ticker):
    # Create the plot with Plotly
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=stock_data.index,
        y=stock_data['Close'],
        mode='lines',
        name=f"{ticker} Closing Prices",
        line=dict(color='#00ffcc'),
        fill='tozeroy',  # Fill area to zero on y-axis
        fillcolor='rgba(0, 255, 204, 0.5)'  # Gradient-like fill color
    ))

    fig.update_layout(
        title=f"{ticker} Stock Prices - Last Month",
        title_font=dict(size=20, color="#ffffff"),  # Custom title font
        xaxis_title="Date",
        yaxis_title="Close Price (USD)",
        xaxis=dict(
            gridcolor="#444",  # Custom grid line color
            zerolinecolor="#666",  # Custom zero line color
            color="#ffcc00"  # Custom axis label color
        ),
        yaxis=dict(
            gridcolor="#444",  # Custom grid line color
            zerolinecolor="#666",  # Custom zero line color
            color="#ffcc00"  # Custom axis label color
        ),
        plot_bgcolor="#1c1c1c",  # Custom plot background
        paper_bgcolor="#262730",  # Custom outer background
        font=dict(color="#ffffff"),  # Custom font color
        template="plotly_dark",  # Base template
        margin=dict(l=10, r=10, t=40, b=10)  # Compact margins
    )

    # Convert Plotly figure to an image and encode as base64
    img_bytes = fig.to_image(format="png", width=700, height=400, scale=2)
    base64_image = base64.b64encode(img_bytes).decode('utf-8')
    return base64_image

# Function to display a styled stock card
def display_stock_card(ticker):
    stock_data = download_stock_data(ticker)
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
        <div class="stock-subtitle">Stock Information - Last Month</div>
        <div class="stock-body">
            <p><strong>Latest Close Price:</strong> ${stock_data['Close'].iloc[-1]:.2f}</p>
            <p><strong>Monthly Return:</strong> {((stock_data['Close'].iloc[-1] - stock_data['Close'].iloc[0]) / stock_data['Close'].iloc[0]) * 100:.2f}%</p>
        </div>
        <div class="stock-plot">
            <img src="data:image/png;base64,{plot_base64}" alt="Stock Plot" />
        </div>
    </div>
    """, unsafe_allow_html=True)

# Streamlit app
st.title("Stock Dashboard")
#ticker = st.text_input("Enter a stock ticker symbol (e.g., AAPL, TSLA):", value="AAPL")

#if ticker:
    #display_stock_card(ticker)


# Main function
def main():
    load_css()
    st.title("Algorithmic Trading Dashboard")

    st.sidebar.header("Select Stocks")
    stock1 = st.sidebar.selectbox("Select Stock 1", ["AAPL", "GOOGL", "MSFT"])
    stock2 = st.sidebar.selectbox("Select Stock 2", ["AAPL", "GOOGL", "MSFT"])
    stock3 = st.sidebar.selectbox("Select Stock 3", ["AAPL", "GOOGL", "MSFT"])

    # Display stock cards
    st.header("Stock Performance")
    col1, col2, col3 = st.columns(3)

    with col1:
        display_stock_card(stock1)

    with col2:
        display_stock_card(stock2)

    with col3:
        display_stock_card(stock3)


if __name__ == "__main__":
    main()