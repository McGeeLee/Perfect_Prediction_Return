import yfinance as yf
import pandas as pd
import streamlit as st

st.title("🔍 Yahoo Finance 数据深度调试")

symbol = st.text_input("输入调试代码", "BTC-USD")
start_date = "2024-01-01"
end_date = "2024-12-31"

if st.button("开始全面检测"):
    try:
        st.write(f"正在请求: {symbol}...")
        # 获取原始数据
        raw_df = yf.download(symbol, start=start_date, end=end_date, progress=False)
        
        if raw_df.empty:
            st.error("❌ 严重错误：Yahoo 返回了空 Dataframe。可能是被限流或代码不存在。")
            st.stop()

        st.success("✅ 成功接收到原始数据")
        
        # 1. 检查列结构
        st.subheader("1. 列结构信息 (Column Structure)")
        st.code(f"列对象类型: {type(raw_df.columns)}")
        st.code(f"原始列名列表: {raw_df.columns.tolist()}")
        
        if isinstance(raw_df.columns, pd.MultiIndex):
            st.info("检测到多层索引 (MultiIndex)")
            for i in range(raw_df.columns.nlevels):
                st.write(f"Level {i} 内容: {raw_df.columns.get_level_values(i).unique().tolist()}")

        # 2. 检查数据前几行
        st.subheader("2. 原始数据预览 (Raw Data)")
        st.dataframe(raw_df.head())

        # 3. 模拟现有的清洗逻辑
        st.subheader("3. 模拟清洗过程")
        test_df = raw_df.copy()
        
        # 尝试压平
        if isinstance(test_df.columns, pd.MultiIndex):
            test_df.columns = test_df.columns.get_level_values(-1)
            st.write("压平后的列名:", test_df.columns.tolist())
        
        test_df = test_df.reset_index()
        st.write("Reset Index 后的列名:", test_df.columns.tolist())

    except Exception as e:
        st.exception(e)
