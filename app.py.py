import streamlit as st
import os
import json
import urllib.request

# 【强制修改底层环境变量】
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['LANG'] = 'C.UTF-8'

st.title("🎨 AI 绘画工作室（真实生成版）")
prompt = st.text_input("请输入你想要的画面：")

if st.button("开始绘画") and prompt:
    # 【核心防御】：把中文强制转成 \uXXXX 的纯 ASCII 编码，服务器底层就不会报错了
    payload_dict = {
        "model": "cogview-3-flash",
        "prompt": prompt
    }
    payload_str = json.dumps(payload_dict, ensure_ascii=True) 
    
    api_key = os.getenv("ZHIPU_API_KEY")
    url = "https://open.bigmodel.cn/api/paas/v4/images/generations"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    req = urllib.request.Request(url, data=payload_str.encode('utf-8'), headers=headers, method='POST')
    
    with st.spinner("AI 正在疯狂作画中..."):
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                image_url = result['data'][0]['url']
                
                st.success("🎉 画作完成！")
                st.image(image_url, caption=prompt)
                
        except Exception as e:
            # 【核心防御】：防止错误信息里带中文导致前端崩溃
            err_msg = str(e).encode('ascii', 'ignore').decode('ascii')
            st.error(f"生成失败了，报错信息：{err_msg}")