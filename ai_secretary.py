import os
import chromadb
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# 1. 连接两个大模型
# DeepSeek 负责聊天和做判断
client_chat = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)
# 智谱 负责把文字变向量（查知识库用）
client_embed = OpenAI(
    api_key=os.getenv("ZHIPU_API_KEY"),
    base_url="https://open.bigmodel.cn/api/paas/v4/" 
)

# 2. 连接你的本地知识库
db_client = chromadb.PersistentClient(path="./chroma_db")
collection = db_client.get_or_create_collection(name="tax_knowledge")

# 3. 定义一个计算器工具（你昨天写过的）
def calculator(a, b):
    return a + b

print("🌟 财税智能小秘书已上线！（输入 '退出' 结束聊天）")

while True:
    user_input = input("\n👤 你问：")
    if user_input == "退出":
        print("👋 再见！")
        break

    # 4. 第一步：让大模型判断你的意图
    prompt_intent = f"""
    请判断用户的意图。
    - 如果涉及税务、研发费用、查资料，请输出：rag
    - 如果是算数学题（包含加减乘除），请输出：math
    - 如果是其他日常闲聊，请输出：chat
    只输出这三个词中的一个，不要任何解释。

    用户说：{user_input}
    """
    res = client_chat.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt_intent}]
    )
    intent = res.choices[0].message.content.strip()

    # 5. 第二步：根据意图分发任务
    if intent == "rag":
        print("🔍 [系统日志] 触发知识库检索...")
        # 把问题变成向量去查
        q_res = client_embed.embeddings.create(model="embedding-3", input=user_input)
        q_vector = q_res.data[0].embedding
        results = collection.query(query_embeddings=[q_vector], n_results=1)
        best_chunk = results['documents'][0][0]
        
        # 让 DeepSeek 结合资料回答
        prompt_rag = f"背景资料：{best_chunk}\n\n请根据资料回答：{user_input}"
        answer = client_chat.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt_rag}]
        ).choices[0].message.content
        print(f"🤖 秘书：{answer}")

    elif intent == "math":
        print("🧮 [系统日志] 触发计算器...")
        try:
            num1 = int(input("请输入第一个数字："))
            num2 = int(input("请输入第二个数字："))
            result = calculator(num1, num2)
            print(f"🤖 秘书：计算结果是 {result}")
        except ValueError:
            print("🤖 秘书：你输入的不是纯数字，我不算啦！")

    else:
        print("💬 [系统日志] 触发闲聊模式...")
        answer = client_chat.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": user_input}]
        ).choices[0].message.content
        print(f"🤖 秘书：{answer}")