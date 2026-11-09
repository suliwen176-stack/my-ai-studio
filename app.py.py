import streamlit as st
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

st.title("🎨 AI 绘画工作室（真实生成版）")
prompt = st.text_input("请输入你想要的画面：")

if st.button("开始绘画") and prompt:
    st.info(f"已收到提示词：{prompt}")
    
    with st.spinner("AI 正在疯狂作画中，请稍候..."):
        try:
            api_key = os.getenv("ZHIPU_API_KEY")
            url = "https://open.bigmodel.cn/api/paas/v4/images/generations"
            
            payload_dict = {
                "model": "cogview-3-flash",
                "prompt": prompt
            }
            
            # 【核心修复】：ensure_ascii=True 会把中文转成 \uXXXX 格式的英文字符
            payload_str = json.dumps(payload_dict, ensure_ascii=True) 
            payload_bytes = payload_str.encode('utf-8')
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, headers=headers, data=payload_bytes)
            response.raise_for_status()
            
            data = response.json()
            image_url = data['data'][0]['url']
            
            st.success("🎉 画作完成！")
            st.image(image_url, caption=prompt)
            
        except Exception as e:
            st.error(f"生成失败了，报错信息：{e}")