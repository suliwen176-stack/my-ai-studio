import requests
import streamlit as st
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(
    api_key=os.getenv("ZHIPU_API_KEY"),
    base_url="https://open.bigmodel.cn/api/paas/v4/"
)

st.title("🎨 AI 绘画工作室（真实生成版）")
prompt = st.text_input("请输入你想要的画面：")

if st.button("开始绘画") and prompt:
    st.info(f"已收到提示词：{prompt}")
    
    with st.spinner("AI 正在疯狂作画中，请稍候..."):
        try:
            # 核心：调用智谱的免费生图模型
            response = client.images.generate(   # 这里由 generations 改为 generate
                model="cogview-3-flash",
                prompt=prompt
            )
            
            image_url = response.data[0].url
            st.success("🎉 画作完成！")
                        # 把图片下载下来
            image_data = requests.get(image_url).content
            with open("my_ai_drawing.jpg", "wb") as f:
                f.write(image_data)
            
            st.image(image_url, caption=prompt)
            
        except Exception as e:
            st.error(f"生成失败了，报错信息：{e}")