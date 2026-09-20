import os
import json

from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime

# ==========================
# 1. 读取 API Key
# ==========================

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)


# ==========================
# 2. 真正由 Python 执行的工具
# ==========================

def calculator(a, b, operation):

    if operation == "add":
        return a + b

    elif operation == "subtract":
        return a - b

    elif operation == "multiply":
        return a * b

    elif operation == "divide":

        if b == 0:
            return "错误：不能除以0"

        return a / b

    else:
        return "错误：未知运算"


def get_current_time():
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")


# ==========================
# 3. 给大模型看的工具说明书
# ==========================

tools = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "执行两个数字之间的加减乘除运算",
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


# ==========================
# 4. 对话历史
# ==========================

messages = [
    {
        "role": "system",
        "content": (
            "你是一个AI助手。"
            "遇到适合计算器处理的数学运算时，请调用calculator工具。"
            "询问当前日期或时间时调用get_current_time工具。"
        )
    }
]

print("正在运行文件：", __file__)

print(
    "当前注册的工具：",
    [tool["function"]["name"] for tool in tools]
)

print("Agent 已启动。")
print("输入“退出”可以结束程序。\n")


# ==========================
# 5. Agent 主循环
# ==========================

while True:

    user_input = input("你：").strip()

    if user_input == "退出":
        print("Agent：再见！")
        break


    # 把用户的话加入历史记录
    messages.append(
        {
            "role": "user",
            "content": user_input
        }
    )


    # ==========================
    # 6. 工具调用循环
    # ==========================

    while True:

        response = client.chat.completions.create(
            model="deepseek-flash",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        assistant_message = response.choices[0].message


        # 把模型的决定加入历史
        messages.append(
            assistant_message.model_dump(
                exclude_none=True
            )
        )


        # ==========================
        # 模型不需要工具
        # ==========================

        if not assistant_message.tool_calls:

            print(
                "\nAgent：",
                assistant_message.content
            )

            print()

            break


        # ==========================
        # 模型要求调用工具
        # ==========================

        for tool_call in assistant_message.tool_calls:

            function_name = tool_call.function.name

            arguments = json.loads(
                tool_call.function.arguments
            )


            print("\n[模型决定调用工具]")

            print(
                "工具：",
                function_name
            )

            print(
                "参数：",
                arguments
            )


            # ==========================
            # 真正执行 Python 函数
            # ==========================

            if function_name == "calculator":

                result = calculator(
                    arguments["a"],
                    arguments["b"],
                    arguments["operation"]
                )

            elif function_name == "get_current_time":

                result = get_current_time()

            else:

                result = "错误：未知工具"


            print(
                "Python 工具执行结果：",
                result
            )

            # ==========================
            # 把工具结果交回模型
            # ==========================

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result)
                }
            )