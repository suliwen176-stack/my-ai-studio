import os
import chromadb
from openai import OpenAI
from dotenv import load_dotenv
from pypdf import PdfReader

load_dotenv()

# 1. 连接智谱（负责向量化）
client_embed = OpenAI(
    api_key=os.getenv("ZHIPU_API_KEY"),
    base_url="https://open.bigmodel.cn/api/paas/v4/" 
)

# 2. 连接 DeepSeek（负责生成回答）
client_chat = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# 3. 初始化 ChromaDB 数据库（数据会存在当前目录的 chroma_db 文件夹里）
db_client = chromadb.PersistentClient(path="./chroma_db")
collection = db_client.get_or_create_collection(name="tax_knowledge")

# ================= 阶段一：建库 =================
if collection.count() == 0:
    print("数据库为空，正在读取 PDF 并构建知识库...")
    reader = PdfReader("test.pdf")
    full_text = "".join([page.extract_text() for page in reader.pages if page.extract_text()])
    
    # 切块（每 500 个字一块）
    chunks = [full_text[i:i+500] for i in range(0, len(full_text), 500)]
    
    print(f"正在将 {len(chunks)} 个文本块转化为向量，请稍候...")
    chunk_vectors = []
    for chunk in chunks:
        res = client_embed.embeddings.create(model="embedding-3", input=chunk)
        chunk_vectors.append(res.data[0].embedding)
    
    # 存入 ChromaDB
    collection.add(
        documents=chunks,
        embeddings=chunk_vectors,
        ids=[f"id_{i}" for i in range(len(chunks))]
    )
    print("✅ 知识库构建完成，并已永久保存！\n")
else:
    print("✅ 发现已存在的知识库，跳过建库步骤。\n")

# ================= 阶段二：检索与问答 =================
question = "税务局查研发的时候，主要看哪些核心要素？"
print(f"你的问题是：{question}")

# 1. 把问题变成向量
q_res = client_embed.embeddings.create(model="embedding-3", input=question)
q_vector = q_res.data[0].embedding

# 2. 去 ChromaDB 里搜（这行代码代替了昨天的 for 循环算距离）
results = collection.query(
    query_embeddings=[q_vector],
    n_results=1  # 只要最相似的一块
)

best_chunk = results['documents'][0][0]
print(f"\n🔍 从数据库匹配到的段落：\n{best_chunk}\n")

# 3. 让 DeepSeek 结合资料生成回答
print("🤖 正在生成回答...")
prompt = f"请根据以下背景资料回答我的问题。\n\n资料：{best_chunk}\n\n问题：{question}"
response = client_chat.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": prompt}]
)

print(f"\n💡 最终回答：\n{response.choices[0].message.content}")