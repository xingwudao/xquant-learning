# Spec: 获取沪深300ETF历史数据

> 所有命令在沙箱外运行。

## 上下文

学员已完成环境配置（Python 3.12 + 虚拟环境 + 依赖包已安装）。这是课程的第一个操作步骤。

## 任务

1. 在当前工作目录下创建 Jupyter Notebook 文件 `q1-strategy.ipynb` 并打开它
2. 在 notebook 中创建代码单元格，获取沪深300ETF最近5年的历史日线数据并可视化

## 要求

1. 导入所需库：yfinance, pandas, numpy, matplotlib.pyplot
2. 设置 matplotlib 中文显示支持：
   - macOS 字体优先使用 Arial Unicode MS，备选 STHeiti
   - Windows 字体使用 SimHei
   - 设置 `axes.unicode_minus = False` 解决负号显示问题
3. 使用 yfinance 获取数据：
   - 标的代码：510300.SS（上交所沪深300ETF）
   - 起始日期：2021-01-01（获取最近约5年数据），不指定结束日期（默认到最新）
   - 传入参数 `auto_adjust=True, multi_level_index=False` 避免警告和多级列名
4. 将数据存储在变量 `df` 中
5. 确保索引为 DatetimeIndex，列名包含 Close

## 结果呈现

1. 打印数据的前 5 行
2. 打印数据时间范围（起始日期 到 结束日期）和总行数
3. 画一条收盘价（Close）折线图，标题为「沪深300ETF (510300) 收盘价走势」
