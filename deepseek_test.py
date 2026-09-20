import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

response = client.chat.completions.create(
    model="deepseek-flash",
    messages=[
        {
            "role": "system",
            "content": "你是一名耐心的老师。"
        },
        {
            "role": "user",
            "content": "请用简单的话告诉我：如何在当今时代学习好使用AI工具，让它服务于日常，极大简化我们的工作流程？"
        }
    ]
)

print(response.choices[0].message.content)
