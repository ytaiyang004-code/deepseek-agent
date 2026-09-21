import os
import json
import httpx
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI

from math_tools import (
    math_calculator,
    track_stagger,
    track_stagger_batch
)


load_dotenv()

client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)


# ==========================
# Token 用量统计
# ==========================

def create_usage_counter():

    return {
        "requests": 0,
        "prompt": 0,
        "completion": 0,
        "total": 0,
        "cache_hit": 0,
        "cache_miss": 0,
        "reasoning": 0
    }


def add_usage(counter, response):

    usage = response.usage

    if usage is None:
        return


    counter["requests"] += 1

    counter["prompt"] += (
        usage.prompt_tokens or 0
    )

    counter["completion"] += (
        usage.completion_tokens or 0
    )

    counter["total"] += (
        usage.total_tokens or 0
    )


    counter["cache_hit"] += (
        getattr(
            usage,
            "prompt_cache_hit_tokens",
            0
        )
        or 0
    )


    counter["cache_miss"] += (
        getattr(
            usage,
            "prompt_cache_miss_tokens",
            0
        )
        or 0
    )


    details = getattr(
        usage,
        "completion_tokens_details",
        None
    )

    if details:

        counter["reasoning"] += (
            getattr(
                details,
                "reasoning_tokens",
                0
            )
            or 0
        )

def print_usage(counter):

    print("\n========== 本轮 API 用量 ==========")

    print(
        "API请求次数：",
        counter["requests"]
    )

    print(
        "输入 Tokens：",
        counter["prompt"]
    )

    print(
        "输出 Tokens：",
        counter["completion"]
    )

    print(
        "推理 Tokens：",
        counter["reasoning"]
    )

    print(
        "缓存命中：",
        counter["cache_hit"]
    )

    print(
        "缓存未命中：",
        counter["cache_miss"]
    )

    print(
        "总 Tokens：",
        counter["total"]
    )

    print("=================================\n")

def get_deepseek_balance():
    try:

        response = httpx.get(
            "https://api.deepseek.com/user/balance",
            headers={
                "Authorization":
                    f"Bearer {os.environ.get('DEEPSEEK_API_KEY')}"
            },

            timeout=10.0
        )


        response.raise_for_status()

        data = response.json()


        for balance in data.get(
            "balance_infos",
            []
        ):

            if balance["currency"] == "CNY":

                return {
                    "available":
                        data["is_available"],

                    "total":
                        balance["total_balance"],

                    "granted":
                        balance["granted_balance"],

                    "topped_up":
                        balance["topped_up_balance"]
                }


    except Exception as error:

        return {
            "error": str(error)
        }


# ==========================
# 时间工具
# ==========================

def get_current_time():
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")

# ==========================
# 工具定义（唯一数据源）
# 每个工具把“给模型看的说明”和“真正执行的 Python 函数”放在一起，
# tools 和 tool_registry 都由这里派生，新增工具只需要改这一个列表。
# ==========================

TOOL_SPECS = [
    {
        "callable": math_calculator,
        "description": "计算数学表达式，支持加减乘除、幂、pi、sqrt、sin、cos等数学运算。",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "要计算的数学表达式，例如：2 * pi * 36.8 + 2 * 84.39"
                }
            },
            "required": ["expression"]
        }
    },

    {
        "callable": track_stagger,
        "description": "计算标准田径跑道不同道次相对于第一道的弯道错位距离。",
        "parameters": {
            "type": "object",
            "properties": {
                "lane": {
                    "type": "integer",
                    "description": "跑道道次，例如2表示第二道"
                },
                "arc_fraction": {
                    "type": "number",
                    "description": "需要计算的弯道比例。1.0表示两个半圆合计，0.5表示一个半圆。"
                },
                "lane_width": {
                    "type": "number",
                    "description": "每条跑道宽度，默认1.22米"
                },
                "curb_radius": {
                    "type": "number",
                    "description": "第一道内沿半径，默认36.5米"
                }
            },
            "required": ["lane"]
        }
    },


    {
        "callable": track_stagger_batch,
        "description": (
            "批量计算多个标准田径跑道道次相对于第一道的弯道错位距离。"
            "需要比较多个道次时，优先使用这个工具，"
            "不要逐个重复调用track_stagger。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "lanes": {
                    "type": "array",
                    "items": {
                        "type": "integer"
                    },
                    "description": "需要计算的道次，例如 [2, 5, 8]"
                },
                "arc_fraction": {
                    "type": "number",
                    "description": "1.0表示完整两个半圆，0.5表示一个半圆"
                },
                "lane_width": {
                    "type": "number",
                    "description": "跑道宽度，默认1.22米"
                },
                "curb_radius": {
                    "type": "number",
                    "description": "第一道内沿半径，默认36.5米"
                }
            },
            "required": ["lanes"]
        }
    },


    {
        "callable": get_current_time,
        "description": "获取当前电脑的本地日期和时间。",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
]


def build_tools(tool_specs):
    """
    把工具定义转换成 DeepSeek API 需要的 tools 参数。
    工具名直接取自 Python 函数名，避免和注册表写得不一样。
    """

    return [
        {
            "type": "function",
            "function": {
                "name": spec["callable"].__name__,
                "description": spec["description"],
                "parameters": spec["parameters"]
            }
        }
        for spec in tool_specs
    ]


def build_tool_registry(tool_specs):
    """
    把工具定义转换成 “工具名 -> Python 函数” 的注册表。
    """

    return {
        spec["callable"].__name__: spec["callable"]
        for spec in tool_specs
    }


tools = build_tools(TOOL_SPECS)

tool_registry = build_tool_registry(TOOL_SPECS)

# ==========================
# 对话历史
# ==========================

messages = [
    {
        "role": "system",
        "content": (
            "你是一个AI助手。"
            "遇到数学表达式时优先使用 math_calculator。"
            "遇到标准田径跑道的分道、弯道错位等几何问题时，"
            "优先使用 track_stagger。"
            "询问当前日期或时间时使用 get_current_time。"
            "工具返回结果后，再结合结果回答用户。"
            "默认使用相对简洁的回答，除非用户明确要求详细推导。"
            "你正在 VS Code 终端中回答用户。"
            "不要使用 LaTeX 公式语法，例如 $...$、\\frac、\\cdot。"
            "数学公式请使用普通文本和 Unicode 符号，例如 π、×、÷、√、²。"
            "复杂公式请单独换行，并简要解释变量含义。"
            "如果需要比较多个跑道道次，优先使用track_stagger_batch。"
            "不要为了多个道次反复调用track_stagger。"
            "如果工具已经返回足以回答问题的数据，不要为了验证相同结论重复调用工具。"
            "同一组道次和相同arc_fraction不要重复调用track_stagger_batch。"
        )
    }
]


MAX_TOOL_STEPS = 6

def main():

    # messages 会在历史裁剪时被整体替换，这里沿用模块级的同一份历史
    global messages

    print("Agent v2 已启动。")
    print("输入“退出”可以结束程序。\n")

    while True:

        user_input = input("你：").strip()

        if user_input == "退出":
            print("Agent：再见！")
            break

        # 本轮 Token 计数器
        usage_counter = create_usage_counter()

        # 加入用户消息
        messages.append(
            {
                "role": "user",
                "content": user_input
            }
        )

        # 本轮临时消息
        working_messages = messages.copy()

        tool_steps = 0
        tool_call_counter = {}

        api_failed = False



        # ==========================
        # Agent 工具调用循环
        # ==========================

        while True:

            try:

                response = client.chat.completions.create(
                    model="deepseek-flash",
                    messages=working_messages,
                    tools=tools,
                    tool_choice="auto",
                    reasoning_effort="none",
                    max_tokens=1200
                )

            except Exception as error:

                # 网络抖动、限流、超时等不应该让整个对话结束
                print(
                    "\nAgent：调用 DeepSeek API 失败：",
                    error
                )

                print("本次提问已取消，请稍后重新提问。\n")

                api_failed = True

                break

            # 记录本次 API Token
            add_usage(
                usage_counter,
                response
            )

            assistant_message = (
                response.choices[0].message
            )

            # 把模型的决定加入临时历史
            working_messages.append(
                assistant_message.model_dump(
                    exclude_none=True
                )
            )


            # ==========================
            # 不需要调用工具
            # ==========================

            if not assistant_message.tool_calls:

                final_answer = (
                    assistant_message.content
                    or ""
                )

                print(
                    "\nAgent：",
                    final_answer
                )

                # 长期历史只保存最终回答
                messages.append(
                    {
                        "role": "assistant",
                        "content": final_answer
                    }
                )

                break


            # ==========================
            # 防止无限调用工具
            # ==========================

            tool_steps += 1

            if tool_steps > MAX_TOOL_STEPS:

                print(
                    "\nAgent：工具调用次数过多，"
                    "本轮已自动停止。"
                )

                break


            # ==========================
            # 执行模型要求的工具
            # ==========================

            for tool_call in assistant_message.tool_calls:

                function_name = (
                    tool_call.function.name
                )

                tool_call_counter[function_name] = (tool_call_counter.get(function_name, 0) + 1)

                # 解析模型给的参数，非法 JSON 不应该把整个程序带崩
                arguments = None
                arguments_error = None

                try:

                    arguments = json.loads(
                        tool_call.function.arguments
                    )

                except (json.JSONDecodeError, TypeError) as error:

                    arguments_error = str(error)


                print(
                    "\n[模型决定调用工具]"
                )

                print(
                    "工具：",
                    function_name
                )

                if arguments_error is None:

                    print(
                        "参数：",
                        arguments
                    )

                else:

                    print(
                        "参数（原始文本）：",
                        tool_call.function.arguments
                    )


                # 查找 Python 中真正的函数
                if arguments_error is not None:

                    result = {
                        "error":
                        f"工具参数不是合法 JSON：{arguments_error}"
                    }

                elif function_name not in tool_registry:

                    result = {
                        "error":
                        f"未知工具：{function_name}"
                    }

                else:

                    try:

                        function = tool_registry[
                            function_name
                        ]

                        result = function(
                            **arguments
                        )

                    except Exception as error:

                        result = {
                            "error": str(error)
                        }


                print(
                    "Python 工具执行结果：",
                    result
                )


                # 把结果转换成字符串
                if isinstance(
                    result,
                    (dict, list)
                ):

                    tool_content = json.dumps(
                        result,
                        ensure_ascii=False
                    )

                else:

                    tool_content = str(result)


                # 把工具结果交还 DeepSeek
                working_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id":
                            tool_call.id,
                        "content":
                            tool_content
                    }
                )
            # ==========================
        # 本轮统计
        # ==========================

        # API 调用失败时本轮没有有效结果，跳过统计直接进入下一轮
        if api_failed:

            continue


        print("\n========== 本轮工具调用 ==========")

        if tool_call_counter:
            total_tool_calls = 0
            for tool_name, count in tool_call_counter.items():

                print(
                    f"{tool_name}：{count} 次"
                )
                total_tool_calls += count
            print("工具调用总数：", total_tool_calls)

        else:
            print("本轮没有调用工具")

        print("================================\n")

        print_usage(
            usage_counter
        )

        balance = get_deepseek_balance()

        print(
            "DeepSeek余额：",
            balance
        )


        # ==========================
        # 控制长期对话历史长度
        # ==========================

        if len(messages) > 9:

            messages = (
                [messages[0]]
                + messages[-8:]
            )


    print("已注册工具：", list(tool_registry.keys()))


if __name__ == "__main__":
    main()

