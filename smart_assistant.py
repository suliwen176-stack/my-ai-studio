import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# 1. 连接大模型（我们请 DeepSeek 当“前台”）
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

print("=== 智能助理已上线 ===")
user_input = input("请输入你的需求：")

# 2. 让大模型判断意图（把它当成一个分类器）
prompt = f"""
请判断下面这句话的意图。
如果用户是想做数学计算，请只输出：math
如果是其他问题，请只输出：chat
不要输出任何其他文字。

用户说：{user_input}
"""

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": prompt}]
)

# 拿到大模型的判断结果（去掉空格和换行）
intent = response.choices[0].message.content.strip()
print(f"🤖 大模型判断意图为：{intent}")

# 3. 根据大模型的判断，走昨天的 if-else 逻辑
if intent == "math":
    print("💡 系统决定：调用计算器模块！")
    # 这里我们简单模拟一下计算
    num1 = int(input("请输入第一个数字："))
    num2 = int(input("请输入第二个数字："))
    print(f"🧮 计算结果：{num1} + {num2} = {num1 + num2}")
    
elif intent == "chat":
    print("💡 系统决定：直接调用大模型闲聊模块！")
    chat_res = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": user_input}]
    )
    print(f"💬 大模型回复：{chat_res.choices[0].message.content}")