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

# ================= 阶段二：多轮对话与问答 =================
# 建立一个列表，用来保存聊天记录（记忆）
messages = [
    {"role": "system", "content": "你是一个专业的财税AI助手，请严格根据我提供的资料回答问题。"}
]

print("🤖 AI 财税助手已上线！输入 '退出' 即可结束对话。\n")

while True:
    # 1. 等待用户输入问题
    question = input("\n👤 你问：")
    if question == "退出":
        print("👋 再见！")
        break

    # 2. 把问题变成向量，去数据库里找资料
    q_res = client_embed.embeddings.create(model="embedding-3", input=question)
    q_vector = q_res.data[0].embedding

    results = collection.query(
        query_embeddings=[q_vector],
        n_results=1
    )
    best_chunk = results['documents'][0][0]

    # 3. 把当前问题和找到的资料，加入记忆列表
    # 巧妙之处：把查到的背景资料，悄悄拼接在用户的问题前面发给 AI
    current_prompt = f"背景资料：{best_chunk}\n\n用户问题：{question}"
    messages.append({"role": "user", "content": current_prompt})

    # 4. 呼叫 DeepSeek 生成回答
    print("🤖 AI 正在思考...")
    response = client_chat.chat.completions.create(
        model="deepseek-chat",
        messages=messages  # 注意这里：把包含历史记录的所有消息发给它
    )

    # 5. 拿到回答，打印出来，并把 AI 的回答也存入记忆
    answer = response.choices[0].message.content
    print(f"\n💡 AI 回答：\n{answer}")
    
    messages.append({"role": "assistant", "content": answer})