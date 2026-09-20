import os
import json

from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI


# 读取 .env
load_dotenv()


# 创建 DeepSeek 客户端
client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)


# =========================
# 我们真正的 Python 工具
# =========================

def calculator(a, b, operation):

    if operation == "add":
        return a + b

    elif operation == "subtract":
        return a - b

    elif operation == "multiply":
        return a * b

    elif operation == "divide":
        if b == 0:
            return "错误：不能除以 0"
        return a / b

    else:
        return "错误：未知运算"

def get_current_time():
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")



# =========================
# 告诉大模型：
# 我们有哪些工具
# =========================

tools = [
    {
        "type": "function",

        "function": {
            "name": "calculator",

            "description": "用于执行两个数字之间的基础数学运算",

            "parameters": {
                "type": "object",

                "properties": {

                    "a": {
                        "type": "number",
                        "description": "第一个数字"
                    },

                    "b": {
                        "type": "number",
                        "description": "第二个数字"
                    },

                    "operation": {
                        "type": "string",
                        "enum": [
                            "add",
                            "subtract",
                            "multiply",
                            "divide"
                        ],
                        "description": "需要执行的运算"
                    }
                },

                "required": [
                    "a",
                    "b",
                    "operation"
                ]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "获取当前电脑的本地日期和时间",
            "parameters": {
                "type": "object",
                "properties": {}
        }
      }
    }
]

print(
    "当前注册的工具：",
    [tool["function"]["name"] for tool in tools]
)

# =========================
# 用户输入
# =========================

question = input("你：")


messages = [
    {
        "role": "system",
        "content": (
        "你是一个AI助手。请根据用户的问题选择合适的工具。"
        "数学运算可以调用calculator工具，"
        "询问当前日期或时间时调用get_current_time工具。"
        )
    },

    {
        "role": "user",
        "content": question
    }
]


# =========================
# 第一次询问 DeepSeek
# =========================

response = client.chat.completions.create(
    model="deepseek-flash",
    messages=messages,
    tools=tools,
    tool_choice="auto"
)


assistant_message = response.choices[0].message


# 把模型的决定加入历史记录
messages.append(
    assistant_message.model_dump(exclude_none=True)
)


# =========================
# 看模型有没有要求调用工具
# =========================

if assistant_message.tool_calls:

    for tool_call in assistant_message.tool_calls:

        # 模型决定调用哪个函数
        function_name = tool_call.function.name

        # 模型给出的参数
        arguments = json.loads(
            tool_call.function.arguments
        )

        print("\n模型决定调用工具：")
        print(function_name)

        print("\n模型给出的参数：")
        print(arguments)


        # 真正执行 Python 函数
        if function_name == "calculator":

            result = calculator(
                arguments["a"],
                arguments["b"],
                arguments["operation"]
            )

        elif function_name == "get_current_time":
            result = get_current_time()

        print("\nPython 工具计算结果：")
        print(result)

        # 把工具运行结果交回 DeepSeek
        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result)
            }
        )


    # =========================
    # DeepSeek 拿到工具结果后
    # 再生成最终答案
    # =========================

    final_response = client.chat.completions.create(
        model="deepseek-flash",
        messages=messages,
        tools=tools
    )


    print("\nAgent：")
    print(
        final_response.choices[0].message.content
    )


else:

    # 不需要工具，直接回答
    print("\nAgent：")
    print(assistant_message.content)