import streamlit as st
import os
import json
import urllib.request

# 页面配置：设置标题和宽屏模式
st.set_page_config(page_title="AI 绘画工作室", page_icon="🎨", layout="wide")

# 强制修改底层环境变量
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['LANG'] = 'C.UTF-8'

# ================= 侧边栏 =================
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/000000/paint-palette.png", width=80)
    st.title("关于工作室")
    st.info("这是一个基于 智谱 CogView 模型驱动的 AI 绘画应用。输入你的想象，让 AI 帮你变成现实。")
    
    st.divider()
    st.markdown("### 💡 灵感提示词")
    st.markdown("- `赛博朋克城市，霓虹灯闪烁`")
    st.markdown("- `水墨画风格的老虎，极简主义`")
    st.markdown("- `一只穿着宇航服的柴犬，在月球漫步`")

# ================= 主界面 =================
st.title("🎨 AI 绘画工作室")
st.caption("输入一句话，创造一幅画。")

# 把输入框和按钮放在一行 (使用 columns 分栏)
col1, col2 = st.columns([4, 1])

with col1:
    prompt = st.text_input("", placeholder="请在这里输入你想要的画面（例如：赛博朋克风格的城市，霓虹灯闪烁，下着雨）...", label_visibility="collapsed")

with col2:
    # 使用 type="primary" 让按钮变成主色调
    generate_btn = st.button("开始绘画", type="primary", use_container_width=True)

if generate_btn and prompt:
    with st.spinner("🎨 AI 正在疯狂作画中，请稍候..."):
        try:
            api_key = os.getenv("ZHIPU_API_KEY").strip()
            url = "https://open.bigmodel.cn/api/paas/v4/images/generations"
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "cogview-3-flash",
                "prompt": prompt
            }
            
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers=headers, method='POST')
            
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
            
            image_url = result['data'][0]['url']
            
            st.success("🎉 画作完成！")
            
            # 使用 st.container 居中显示图片
            st.image(image_url, caption=prompt, use_column_width=True)
            
            # 添加下载按钮
            st.markdown(f"[📥 点击这里下载高清大图]({image_url})")
            
        except Exception as e:
            err_msg = str(e).encode('ascii', 'ignore').decode('ascii')
            st.error(f"生成失败了，报错信息：{err_msg}")