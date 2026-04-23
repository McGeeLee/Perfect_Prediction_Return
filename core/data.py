import tushare as ts
import yfinance as yf
import pandas as pd

def detect_asset(symbol):
    """识别资产类型和数据源"""
    symbol = symbol.upper()

    # ===== Crypto / 美股 =====
    if "-USD" in symbol or any(c.isalpha() for c in symbol) and "." not in symbol:
        return "global", "Yahoo"

    # ===== A股 / ETF =====
    if symbol.endswith(".SH") or symbol.endswith(".SZ"):
        code = symbol.split(".")[0]
        if code.startswith("51"):
            return "etf", "Tushare"
        elif code.startswith(("6", "0", "3")):
            return "stock", "Tushare"

    # 默认尝试 Yahoo
    return "other", "Yahoo"


def format_date_for_yahoo(date_str):
    """把 20250101 → 2025-01-01"""
    if "-" not in date_str and len(date_str) == 8:
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    return date_str


def get_data(symbol, start, end, token=None):
    asset_type, source = detect_asset(symbol)
    print(f"识别: {asset_type} | 数据源: {source}")

    # =========================
    # Tushare 数据源 (A股/ETF)
    # =========================
    if source == "Tushare":
        if not token:
            print("错误: 未提供 Tushare Token")
            return pd.DataFrame()
        
        ts.set_token(token)
        pro = ts.pro_api()

        try:
            if asset_type == "stock":
                df = pro.daily(ts_code=symbol, start_date=start, end_date=end)
            elif asset_type == "etf":
                df = pro.fund_daily(ts_code=symbol, start_date=start, end_date=end)
            else:
                return pd.DataFrame()

            if df is None or df.empty:
                print("Tushare 返回数据为空")
                return pd.DataFrame()

            # 整理 Tushare 格式
            df = df.sort_values("trade_date")
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            df.rename(columns={'open': 'Open', 'close': 'Close'}, inplace=True)
            return df[['trade_date', 'Open', 'Close']]

        except Exception as e:
            print(f"Tushare 接口报错: {e}")
            return pd.DataFrame()

    # =========================
    # Yahoo 数据源 (Crypto/美股)
    # =========================
    else:
        start_yf = format_date_for_yahoo(start)
        end_yf = format_date_for_yahoo(end)

        try:
            # 下载数据
            df = yf.download(
                symbol,
                start=start_yf,
                end=end_yf,
                interval="1d",
                progress=False,
                auto_adjust=True  # 自动调整 OHLC
            )

            if df is None or df.empty:
                print(f"Yahoo 无法获取数据: {symbol}")
                return pd.DataFrame()

            # --- 关键：清洗 MultiIndex 或冗余列名 ---
            # 如果是多级索引，压平它
            if isinstance(df.columns, pd.MultiIndex):
                # 寻找包含核心词的那一层
                df.columns = [col[-1] if col[-1] != '' else col[0] for col in df.columns]
            
            df = df.reset_index()
            
            # 统一清理列名中的空格
            df.columns = [str(c).strip() for c in df.columns]

            # 寻找 Date, Open, Close (不区分大小写)
            rename_dict = {}
            for col in df.columns:
                c_low = col.lower()
                if "date" in c_low: rename_dict[col] = "trade_date"
                if "open" in c_low: rename_dict[col] = "Open"
                if "close" in c_low: rename_dict[col] = "Close"
            
            df.rename(columns=rename_dict, inplace=True)

            # 检查列是否凑齐
            required = ["trade_date", "Open", "Close"]
            if not all(col in df.columns for col in required):
                print(f"解析后的列名异常，当前列: {df.columns.tolist()}")
                return pd.DataFrame()

            # 清洗日期格式
            df['trade_date'] = pd.to_datetime(df['trade_date']).dt.tz_localize(None)
            
            # 排序并只返回需要的列
            df = df.sort_values("trade_date")
            return df[required]

        except Exception as e:
            print(f"Yahoo 数据解析报错: {e}")
            return pd.DataFrame()
