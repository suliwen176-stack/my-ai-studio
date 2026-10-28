import os
from openai import OpenAI
from dotenv import load_dotenv

# 1. 读取隐藏的密码本
load_dotenv()

# 2. 找到服务员，告诉他地址（DeepSeek的地址）和你的通行证
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com" 
)

print("正在呼叫大模型，请稍候...")

# 3. 发送请求（点菜）
response = client.chat.completions.create(
    model="deepseek-chat", # 指定用哪个模型
    messages=[
        {"role": "user", "content": "你好，请用一句话向我介绍什么是Python？"}
    ]
)

# 4. 提取大模型的回答并打印
print("\n大模型的回答是：")
print(response.choices[0].message.content)