import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['LANG'] = 'C.UTF-8'

# 下面是你原来的代码
import streamlit as st
import json
import urllib.request
import urllib.error
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
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "cogview-3-flash",
                "prompt": prompt
            }
            
            # 确保提取出来的数据是 utf-8
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers=headers, method='POST')
            
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
            
            image_url = result['data'][0]['url']
            
            st.success("🎉 画作完成！")
            st.image(image_url, caption=prompt)
            
        except urllib.error.HTTPError as e:
            st.error(f"网络请求失败，状态码：{e.code}，详情：{e.read().decode('utf-8')}")
        except Exception as e:
            st.error(f"生成失败了，报错信息：{e}")