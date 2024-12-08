import streamlit as st
import plotly.express as px
import yfinance as yf
import numpy as np

st.set_page_config(layout="wide")

# Custom CSS for rounded edges
st.markdown(
    """
    <style>
    .card {
        border-radius: 15px;
        padding: 30px;  /* Increased padding */
        background-color: #636EFA;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.5);
        margin: 10px;
        width: 300px;  /* Set a fixed width */
        height: 200px; /* Set a fixed height */
        display: flex; /* Use flexbox to center content */
        flex-direction: column; /* Stack content vertically */
        justify-content: center; /* Center content vertically */
        align-items: center; /* Center content horizontally */
    }
    </style>
    """,
    unsafe_allow_html=True
)


# Function to calculate moving average and returns
def calculate_strategy(stock_data, strategy):
    if strategy == 'mm9':
        # Calculate the 9-day moving average
        stock_data['MA9'] = stock_data['Close'].rolling(window=9).mean()
        stock_data['sinal'] = np.sign(stock_data['MA9'].pct_change())
        # Calculate returns
        stock_data['st_return'] = (stock_data['sinal']*stock_data['return'].shift(-1)).cumsum()
        return stock_data
    else:
        st.error("Strategy not recognized.")
        return None



# Sidebar
st.sidebar.header("Controls")
option = st.sidebar.selectbox("Choose an option", ["Option 1", "Option 2", "Option 3"])
st.sidebar.button("Submit")

# Display the selected option from the sidebar
st.sidebar.write('You selected:', option)

# Title of the app
st.title("Stock Price Viewer")

# Create two columns for user input
col1, col2, col3 = st.columns(3)


# User input for stock ticker in the first column
with col1:
    ticker_input = st.text_input("Enter Stock Ticker (e.g., AAPL, GOOGL):", "AAPL")

# User input for strategy in the second column
with col2:
    strategy_input = st.text_input("Enter Strategy (e.g., mm9):", "mm9")

with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    #st.header("Card 1")
    #st.write("This is the content of card 1.")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    #st.header("Card 2")
    #st.write("This is the content of card 2.")
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    #st.header("Card 3")
    #st.write("This is the content of card 3.")
    st.markdown('</div>', unsafe_allow_html=True)




# Download historical data from Yahoo Finance
if ticker_input:
    stock_data = yf.download(ticker_input, interval="1d", period='5y')
    stock_data['return'] = stock_data['Close'].pct_change()

    # Check if data is available
    if not stock_data.empty:
        # Reset index to make sure the index is a column
        stock_data.reset_index(inplace=True)

        # Calculate strategy
        stock_data = calculate_strategy(stock_data, strategy_input)

        # Create a Plotly figure
        fig = px.line(stock_data, x='Date', y=stock_data['return'].cumsum(), title=f'{ticker_input} Stock Price',template = "plotly_dark")

        # Add moving average to the figure
        if 'st_return' in stock_data.columns:
            fig.add_scatter(x=stock_data['Date'], y=stock_data['st_return'], mode='lines', name='st_return',
                            line=dict(color='orange'))

        st.subheader(f"{ticker_input} Stock Price Chart")
        st.write("This chart shows the closing price of the selected stock over the last 6 months.")
        # Display the Plotly chart inside the card
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.error("No data found for the ticker symbol provided.")