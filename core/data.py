import tushare as ts
import yfinance as yf
import pandas as pd

def detect_asset(symbol):
    """识别资产类型和数据源"""
    symbol = symbol.upper()
    # ===== Crypto / 全球资产 =====
    if "-USD" in symbol or any(c.isalpha() for c in symbol) and "." not in symbol:
        return "global", "Yahoo"
    # ===== A股 / ETF =====
    if symbol.endswith(".SH") or symbol.endswith(".SZ"):
        code = symbol.split(".")[0]
        if code.startswith("51"):
            return "etf", "Tushare"
        elif code.startswith(("6", "0", "3")):
            return "stock", "Tushare"
    return "other", "Yahoo"

def format_date_for_yahoo(date_str):
    """日期格式转换"""
    if "-" not in date_str and len(date_str) == 8:
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    return date_str

def get_data(symbol, start, end, token=None):
    asset_type, source = detect_asset(symbol)
    print(f"识别: {asset_type} | 数据源: {source}")

    if source == "Tushare":
        if not token: return pd.DataFrame()
        ts.set_token(token)
        pro = ts.pro_api()
        try:
            if asset_type == "stock":
                df = pro.daily(ts_code=symbol, start_date=start, end_date=end)
            elif asset_type == "etf":
                df = pro.fund_daily(ts_code=symbol, start_date=start, end_date=end)
            else: return pd.DataFrame()
            
            if df is None or df.empty: return pd.DataFrame()
            df = df.sort_values("trade_date")
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            df.rename(columns={'open': 'Open', 'close': 'Close'}, inplace=True)
            return df[['trade_date', 'Open', 'Close']]
        except Exception as e:
            print(f"Tushare Error: {e}")
            return pd.DataFrame()

    else:  # Yahoo Source
        start_yf = format_date_for_yahoo(start)
        end_yf = format_date_for_yahoo(end)
        try:
            # 1. 下载数据 (auto_adjust=True 帮助简化 OHLC 结构)
            df = yf.download(symbol, start=start_yf, end=end_yf, interval="1d", progress=False, auto_adjust=True)
            if df is None or df.empty: return pd.DataFrame()

            # 2. 🚀 关键：处理 MultiIndex (解决你日志中那一串 BTC-USD 的问题)
            if isinstance(df.columns, pd.MultiIndex):
                # 无论有多少层，我们只取最后一层，那是 Open/Close 所在的层级
                df.columns = df.columns.get_level_values(-1)
            
            df = df.reset_index()
            
            # 3. 🔍 健壮性增强：列名模糊匹配
            # 遍历所有列名，寻找包含 date, open, close 关键字的列
            new_columns = {}
            for col in df.columns:
                col_name = str(col).lower().strip()
                if "date" in col_name: new_columns[col] = "trade_date"
                elif "open" in col_name: new_columns[col] = "Open"
                elif "close" in col_name: new_columns[col] = "Close"
            
            df.rename(columns=new_columns, inplace=True)

            # 4. 最终检查与清洗
            required = ["trade_date", "Open", "Close"]
            if not all(c in df.columns for c in required):
                print(f"解析失败。当前列名: {list(df.columns)}")
                return pd.DataFrame()

            # 统一日期格式并去除时区，防止绘图出错
            df['trade_date'] = pd.to_datetime(df['trade_date']).dt.tz_localize(None)
            df = df.sort_values("trade_date")
            
            return df[required]
            
        except Exception as e:
            print(f"Yahoo 彻底报错: {e}")
            return pd.DataFrame()
