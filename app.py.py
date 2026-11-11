import streamlit as st
import os
import json
import urllib.request
from openai import OpenAI
from dotenv import load_dotenv

# ================= 1. 极致黑金 CSS 注入 =================
st.set_page_config(page_title="AI 创作工作室", page_icon="✨", layout="centered")

custom_css = """
<style>
    /* 暴力隐藏 Streamlit 所有的开发者痕迹 */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    [data-testid="stToolbar"] {visibility: hidden !important;}
    [data-testid="stDecoration"] {visibility: hidden !important;}
    [data-testid="stStatusWidget"] {visibility: hidden !important;} /* 隐藏右下角 Manage app */
    
    /* 纯黑背景 */
    .stApp {
        background-color: #050505;
        color: #E0E0E0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* 侧边栏隐藏与美化 */
    [data-testid="stSidebar"] {
        background-color: #0A0A0A;
        border-right: 1px solid #1A1A1A;
    }
    
    /* 主区域居中与边距 */
    .block-container {
        padding-top: 5rem;
        padding-bottom: 6rem;
        max-width: 800px;
    }
    
    /* 悬浮输入框（即梦同款发光胶囊） */
    [data-testid="stChatInput"] {
        background-color: #141414 !important;
        border: 1px solid #2A2A2A !important;
        border-radius: 30px !important;
        padding: 12px 24px !important;
        color: white !important;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.8) !important;
        transition: all 0.3s ease;
    }
    [data-testid="stChatInput"]:focus-within {
        border-color: #555 !important;
        box-shadow: 0 4px 40px rgba(255, 255, 255, 0.1) !important;
    }
    
    /* 对话气泡美化（去掉默认的气泡底色，只留文字） */
    [data-testid="stChatMessage"] {
        background-color: transparent !important;
        padding: 10px 0 !important;
        border: none !important;
    }
    
    /* 图片圆角与阴影 */
    .stImage img {
        border-radius: 12px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.6);
        transition: transform 0.3s ease;
    }
    .stImage img:hover {
        transform: translateY(-2px);
    }
    
    /* 隐藏单选框的丑陋圆圈，变成侧边栏高级菜单 */
    div[role="radiogroup"] > label > div:first-child {
        display: none;
    }
    div[role="radiogroup"] > label {
        background-color: #141414;
        padding: 8px 15px;
        border-radius: 12px;
        margin-bottom: 8px;
        border: 1px solid #222;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    div[role="radiogroup"] > label:hover {
        border-color: #555;
        background-color: #1A1A1A;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

load_dotenv()
client_chat = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")

# ================= 2. 侧边栏（极简控制台） =================
with st.sidebar:
    st.markdown("<h3 style='color:#FAFAFA; margin-bottom: 20px;'>✨ AI Studio</h3>", unsafe_allow_html=True)
    
    # 模式选择
    mode = st.radio("当前模式", ["🎬 图文短剧", "🎨 单张绘图"], label_visibility="collapsed")
    
    st.markdown("---")
    # 新建对话按钮
    if st.button("➕ 新建对话", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
        
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    st.caption("v3.0 极简版")

# ================= 3. 主界面对话流 =================
# 首屏欢迎语（如果没有任何对话时显示）
if not st.session_state.get("messages"):
    st.markdown("""
        <div style='text-align: center; margin-top: 10vh; margin-bottom: 10vh;'>
            <h1 style='color: #FFFFFF; font-weight: 300; font-size: 2.5rem; letter-spacing: 2px;'>让想象触手可及</h1>
            <p style='color: #888; font-size: 1.1rem;'>在下方输入您的想法，AI 将为您绘制画面</p>
        </div>
    """, unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

# 渲染历史记录
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["type"] == "text":
            st.markdown(msg["content"])
        elif msg["type"] == "image_list":
            cols = st.columns(3)
            for i, img in enumerate(msg["content"]):
                with cols[i % 3]:
                    st.image(img["url"], caption=img["caption"], use_container_width=True)

# 底部悬浮输入框
user_input = st.chat_input("输入想法、剧本或画面描述，和 Agent 一起创作...")

if user_input:
    # 记录用户输入
    st.session_state.messages.append({"role": "user", "type": "text", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # AI 处理逻辑
    with st.chat_message("assistant"):
        if mode == "🎨 单张绘图":
            with st.spinner("AI 正在绘制..."):
                try:
                    api_key = os.getenv("ZHIPU_API_KEY").strip()
                    url = "https://open.bigmodel.cn/api/paas/v4/images/generations"
                    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                    payload = {"model": "cogview-3-flash", "prompt": user_input}
                    
                    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
                    with urllib.request.urlopen(req) as response:
                        result = json.loads(response.read().decode('utf-8'))
                        img_url = result['data'][0]['url']
                        
                        st.image(img_url, use_container_width=True)
                        st.markdown(f"**[📥 点击下载原图]({img_url})**")
                        
                        st.session_state.messages.append({
                            "role": "assistant", "type": "image_list", 
                            "content": [{"url": img_url, "caption": user_input}]
                        })
                except Exception as e:
                    st.error(f"生成失败：{e}")
                    
        elif mode == "🎬 图文短剧":
            with st.spinner("导演正在拆解剧本..."):
                prompt = f"""你是一个电影分镜师。将剧本拆解为分镜。严格输出JSON：
                [{{"shot_id": 1, "visual_prompt": "英文画面描述", "dialogue": "台词"}}]
                剧本：{user_input}"""
                
                try:
                    res = client_chat.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompt}])
                    clean_json = res.choices[0].message.content.replace("```json", "").replace("```", "").strip()
                    storyboard = json.loads(clean_json)
                except Exception as e:
                    st.error(f"剧本拆解失败：{e}")
                    st.stop()

            st.markdown(f"✅ 拆解完毕！共 {len(storyboard)} 个镜头，正在生成画面...")
            
            cols = st.columns(3)
            images_data = []
            
            for i, shot in enumerate(storyboard):
                with cols[i % 3]:
                    st.caption(f"镜头 {shot['shot_id']}: {shot.get('dialogue', '')}")
                    with st.spinner("绘制中..."):
                        try:
                            api_key = os.getenv("ZHIPU_API_KEY").strip()
                            url = "https://open.bigmodel.cn/api/paas/v4/images/generations"
                            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                            payload = {"model": "cogview-3-flash", "prompt": shot['visual_prompt']}
                            
                            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
                            with urllib.request.urlopen(req) as response:
                                result = json.loads(response.read().decode('utf-8'))
                                img_url = result['data'][0]['url']
                                st.image(img_url, use_container_width=True)
                                images_data.append({"url": img_url, "caption": shot['dialogue']})
                        except Exception as e:
                            pass
            
            st.session_state.messages.append({
                "role": "assistant", "type": "image_list", "content": images_data
            })