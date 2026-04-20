import streamlit as st
from core.data import get_data
from core.strategy import run_strategy
from utils.plot import plot_equity

st.set_page_config(page_title="完美预测系统", layout="wide")

st.title("📊 完美预测交易分析系统")

# =========================
# 参数区
# =========================
st.sidebar.header("⚙️ 参数设置")

symbol = st.sidebar.text_input("资产代码", "518880.SH")

start = st.sidebar.text_input("开始日期", "20150101")
end = st.sidebar.text_input("结束日期", "20250101")

freq = st.sidebar.selectbox("时间粒度", ["Year", "Month", "Day"])

fee = st.sidebar.slider("单边手续费 (%)", 0.0, 1.0, 0.2) / 100

token = st.sidebar.text_input("Tushare Token", type="password")

run = st.sidebar.button("运行")

# =========================
# 主逻辑
# =========================
if run:

    if token == "":
        st.warning("请输入 Tushare Token")

    else:
        st.info("📡 获取数据中...")
        df = get_data(symbol, start, end, token)

        if df.empty:
            st.error(f"数据为空 | symbol={symbol}")
            st.stop()
        else:
            st.success("数据获取成功")

            st.info("⚙️ 运行策略中...")
            result = run_strategy(df, fee, freq)

            st.subheader("📈 核心指标")

            col1, col2, col3 = st.columns(3)

            col1.metric("买入持有", f"{result['bh_cum'].iloc[-1]:.2f} 倍")
            col2.metric("策略收益", f"{result['strategy_cum'].iloc[-1]:.2f} 倍")
            col3.metric("交易占比", f"{result['trade'].mean():.2%}")

            st.subheader("📊 收益曲线")
            fig = plot_equity(result)
            st.pyplot(fig)

            st.subheader("📋 数据明细")
            st.dataframe(result)