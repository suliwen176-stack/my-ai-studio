import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# 1. 读取密码本，连上大模型
load_dotenv()
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com" 
)
# 注意：如果你刚才换了其他平台，记得把上面两行换成你平台的 base_url 和 key

# 2. 假设这是老板发来的一段发票备注
messy_text = "昨天下午去买了一批研发材料，一共花了三千五百块，记得报销。"
print(f"原始脏数据：{messy_text}\n")

# 3. 告诉 AI 需要提取什么（这就是提示词）
# 我们要求它必须返回 JSON 格式！
prompt = f"""
请从下面这段话中提取出“金额”和“费用类别”。
并且严格按照 JSON 格式输出，不要输出任何额外的解释文字。
格式要求：{{"金额": 数字, "费用类别": "文本"}}

原话：{messy_text}
"""

print("AI 正在提取数据...")
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": prompt}]
)

# 4. 拿到 AI 的回答
ai_result = response.choices[0].message.content
print(f"\nAI 返回的原始结果：\n{ai_result}")

# 5. 把 JSON 文本变成真正的 Python 字典
data = json.loads(ai_result)
print(f"\n最终可以直接写入 Excel 的数据：\n{data}")
print(f"提取的金额是：{data['金额']} 元，类型是：{data['费用类别']}")
