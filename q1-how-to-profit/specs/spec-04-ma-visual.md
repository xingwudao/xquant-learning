# Spec: 可视化均线与交叉信号

> 所有命令在沙箱外运行。

## 上下文

在 `q1-strategy.ipynb` 中已有：
- 沪深300ETF 日线数据（变量 `df`，含 Close 列）

上一节引入了均线的概念——过去 N 天收盘价的平均值。接下来要画一张图，让你亲眼看到均线长什么样、交叉发生在哪里。

## 任务

在 notebook 中新建代码单元格，画出收盘价与三条均线的对比图，并标记交叉点。

## 要求

1. 在 notebook 中新建代码单元格
2. 截取最近 1 年数据，让图更清晰：
   ```python
   one_year_ago = df.index[-1] - pd.DateOffset(years=1)
   df_recent = df.loc[one_year_ago:].copy()
   ```
3. 基于 `df_recent` 计算三条均线：
   - `ma10 = df_recent['Close'].rolling(10).mean()`
   - `ma20 = df_recent['Close'].rolling(20).mean()`
   - `ma60 = df_recent['Close'].rolling(60).mean()`
4. 找出收盘价与 MA20 的交叉点：
   - 上穿：前一天 Close <= MA20，当天 Close > MA20
   - 下穿：前一天 Close >= MA20，当天 Close < MA20
5. 画一张对比图（figsize 14×7）：
   - 收盘价（黑色实线，标注"收盘价"）
   - MA10（绿色虚线，标注"10日均线"）
   - MA20（蓝色实线，标注"20日均线"）
   - MA60（红色点线，标注"60日均线"）
   - 上穿点：绿色向上三角标记（marker='^', markersize=10）
   - 下穿点：红色向下三角标记（marker='v', markersize=10）
   - 标题「沪深300ETF：收盘价与均线（最近1年）」
   - 图例 + 网格

## 结果呈现

1. 价格与均线对比图（含交叉点标记）
2. 打印交叉统计：
   ```
   MA20 交叉统计（最近1年）：
     上穿（买入信号）：N 次
     下穿（卖出信号）：N 次
   ```
