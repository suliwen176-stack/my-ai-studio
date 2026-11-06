import os
import streamlit as st
import chromadb
from openai import OpenAI
from dotenv import load_dotenv

# 设置网页的标题和图标
st.set_page_config(page_title="财税智能小秘书", page_icon="🤖")
st.title("🤖 财税智能小秘书")
st.caption("基于 RAG 与 Agent 架构的多功能 AI 助手")

load_dotenv()

# 连接大模型
client_chat = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)
client_embed = OpenAI(
    api_key=os.getenv("ZHIPU_API_KEY"),
    base_url="https://open.bigmodel.cn/api/paas/v4/" 
)

# 连接知识库
db_client = chromadb.PersistentClient(path="./chroma_db")
collection = db_client.get_or_create_collection(name="tax_knowledge")

# 网页里的聊天输入框
user_input = st.chat_input("请在这里输入你的问题...")

if user_input:
    # 1. 显示用户的提问
    with st.chat_message("user"):
        st.write(user_input)

    # 2. 机器人开始思考
    with st.chat_message("assistant"):
        with st.spinner("小秘书正在分析你的意图..."):
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
            st.info(f"系统判定意图：{intent.upper()} 模式")

        # 3. 根据意图执行不同操作
        if intent == "rag":
            with st.spinner("正在翻阅财税知识库..."):
                q_res = client_embed.embeddings.create(model="embedding-3", input=user_input)
                q_vector = q_res.data[0].embedding
                results = collection.query(query_embeddings=[q_vector], n_results=1)
                best_chunk = results['documents'][0][0]
                
                prompt_rag = f"背景资料：{best_chunk}\n\n请根据资料回答：{user_input}"
                answer = client_chat.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": prompt_rag}]
                ).choices[0].message.content
                st.write(answer)

        elif intent == "math":
            with st.spinner("正在计算..."):
                prompt_math = f"请提取这句话里的数字并进行计算，直接告诉我结果。比如输入'50加30'，你直接输出'50 + 30 = 80'。\n用户说：{user_input}"
                answer = client_chat.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": prompt_math}]
                ).choices[0].message.content
                st.write(answer)

        else:
            with st.spinner("正在思考..."):
                answer = client_chat.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": user_input}]
                ).choices[0].message.content
                st.write(answer)