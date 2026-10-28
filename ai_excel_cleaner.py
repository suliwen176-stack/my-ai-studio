import os
import json
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

# 1. 连接大模型
load_dotenv()
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# 2. 读取昨天的脏数据 Excel
print("正在读取 Excel 数据...")
df = pd.read_excel("expense_data.xlsx")

# 3. 找出金额是字符串（文字）的行，这就是昨天的脏数据
# 我们循环遍历表格，把脏数据找出来
for index, row in df.iterrows():
    amount = row["金额"]
    # 如果金额不是数字类型（比如是"三千"），我们就叫 AI 帮忙
    if isinstance(amount, str) and not amount.isdigit():
        print(f"\n发现脏数据（第{index+1}行）：{amount}，呼叫 AI 转换...")
        
        prompt = f"请把下面这句话里的金额转换为纯数字，只返回数字本身，不要任何其他文字：{amount}"
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}]
        )
        
        # 拿到 AI 的回答（纯数字），比如 "3000"
        clean_amount = response.choices[0].message.content.strip()
        print(f"AI 转换成功，转换成数字：{clean_amount}")
        
        # 4. 把 AI 清洗后的数据，替换掉原来表格里的脏数据！
        df.at[index, "金额"] = int(clean_amount)

# 5. 导出干干净净的新表格
df.to_excel("expense_data_cleaned.xlsx", index=False)
print("\n🎉 所有数据清洗完毕！已导出为 expense_data_cleaned.xlsx")