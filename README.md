# DeepSeek Agent - 标准跑道分析小项目

这是一个用于学习 AI Agent 基本原理的入门项目。

项目基于 Python 和 DeepSeek API，从最基础的模型 API 调用开始，逐步实现了 Tool Calling、Agent Loop、多工具调用、Token 统计和针对标准田径跑道问题的计算工具。

## 当前功能

- 使用 DeepSeek API 进行自然语言交互
- Agent 自动判断是否需要调用工具
- 支持多轮 Tool Calling
- 数学表达式计算
- 标准田径跑道弯道错位计算
- 多跑道批量计算
- 当前时间查询
- API Token 使用量统计
- DeepSeek API 余额查询
- 工具调用次数统计
- 简单的对话历史控制

## 主要工具

### math_calculator

用于计算数学表达式，例如：

```text
2 * pi * 36.8 + 2 * 84.39