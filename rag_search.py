import os
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
from pypdf import PdfReader

# 读取密码本
load_dotenv()

# 1. 连接智谱（把文字变成向量）
client_embed = OpenAI(
    api_key=os.getenv("ZHIPU_API_KEY"),
    base_url="https://open.bigmodel.cn/api/paas/v4/" 
)

# 2. 连接 DeepSeek（做最后的回答）
client_chat = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# 3. 读取 PDF 并切块
print("正在读取 PDF 并切块...")
reader = PdfReader("test.pdf")
full_text = ""
for page in reader.pages:
    if page.extract_text(): 
        full_text += page.extract_text() + "\n"

# 每 500 个字切一块
chunk_size = 500
chunks = [full_text[i:i+chunk_size] for i in range(0, len(full_text), chunk_size)]

# 4. 把每一块文字变成向量（使用智谱 embedding-3）
print(f"正在将 {len(chunks)} 个文本块转化为向量，请稍候...")
chunk_vectors = []
for chunk in chunks:
    response = client_embed.embeddings.create(
        model="embedding-3", 
        input=chunk
    )
    chunk_vectors.append(response.data[0].embedding)

# 5. 用户提问，把问题也变成向量
question = "税务局查研发的时候，主要看哪些核心要素？"
print(f"\n你的问题是：{question}")
q_res = client_embed.embeddings.create(
    model="embedding-3",
    input=question
)
q_vector = q_res.data[0].embedding

# 6. 计算问题与每一个文本块的“距离”（找最相似的）
similarities = []
for vec in chunk_vectors:
    sim = np.dot(q_vector, vec) / (np.linalg.norm(q_vector) * np.linalg.norm(vec))
    similarities.append(sim)

# 找出发音最相似的那一块！
best_index = np.argmax(similarities)
best_chunk = chunks[best_index]

print(f"\n🔍 机器最匹配到的段落（相似度 {similarities[best_index]:.2f}）：\n{best_chunk}\n")

# 7. 把匹配到的段落，和问题一起发给 DeepSeek 生成最终回答
print("🤖 DeepSeek 正在根据匹配内容生成回答...")
prompt = f"请根据以下背景资料回答我的问题。\n\n资料：{best_chunk}\n\n问题：{question}"

response = client_chat.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": prompt}]
)

print(f"\n💡 最终回答：\n{response.choices[0].message.content}")