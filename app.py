
import streamlit as st
import pandas as pd
import ccxt
import yfinance as yf
import ta
import plotly.graph_objects as go

def fetch_crypto(symbol="BTC/USDT", timeframe="1h", limit=200):
    exchange = ccxt.binance()
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df

def fetch_stock(symbol="AAPL", interval="1h", period="7d"):
    df = yf.download(tickers=symbol, interval=interval, period=period)
    df.reset_index(inplace=True)
    df.rename(columns={"Date": "timestamp", "Open": "open", "High": "high", "Low": "low",
                       "Close": "close", "Volume": "volume"}, inplace=True)
    return df

def add_indicators(df):
    df["rsi"] = ta.momentum.RSIIndicator(df["close"]).rsi()
    df["adx"] = ta.trend.ADXIndicator(df["high"], df["low"], df["close"]).adx()
    macd = ta.trend.MACD(df["close"])
    df["macd_line"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    df["ema200"] = ta.trend.EMAIndicator(df["close"], window=200).ema_indicator()
    df["vwap"] = (df["volume"] * (df["high"] + df["low"] + df["close"]) / 3).cumsum() / df["volume"].cumsum()
    return df

def get_signal(latest):
    if (
        latest["rsi"] > 50 and
        latest["adx"] > 20 and
        latest["close"] > latest["ema200"] and
        latest["macd_line"] > latest["macd_signal"] and
        latest["close"] > latest["vwap"]
    ):
        return "BUY"
    elif (
        latest["rsi"] < 50 and
        latest["adx"] > 20 and
        latest["close"] < latest["ema200"] and
        latest["macd_line"] < latest["macd_signal"] and
        latest["close"] < latest["vwap"]
    ):
        return "SELL"
    else:
        return "HOLD"

st.title("📈 Smart Trading Strategy Dashboard")
symbol = st.text_input("Enter Symbol (e.g. BTC/USDT or AAPL):", "BTC/USDT")

try:
    if "/" in symbol:
        df = fetch_crypto(symbol)
    else:
        df = fetch_stock(symbol)

    df = add_indicators(df)
    signal = get_signal(df.iloc[-1])
    st.subheader(f"Signal: {signal}")

    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df["timestamp"], open=df["open"], high=df["high"],
                                 low=df["low"], close=df["close"], name="Price"))
    fig.add_trace(go.Scatter(x=df["timestamp"], y=df["ema200"], line=dict(color="blue", width=1), name="EMA200"))
    fig.add_trace(go.Scatter(x=df["timestamp"], y=df["vwap"], line=dict(color="purple", width=1), name="VWAP"))
    st.plotly_chart(fig)

    st.write("Latest Indicators:")
    st.dataframe(df[["timestamp", "rsi", "adx", "macd_line", "macd_signal", "ema200", "vwap"]].tail(5))
except Exception as e:
    st.error(f"Error: {e}")
