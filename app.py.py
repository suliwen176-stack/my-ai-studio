import streamlit as st
import os
import json
import urllib.request
from openai import OpenAI
from dotenv import load_dotenv

# ================= 1. 注入极致即梦风 CSS =================
st.set_page_config(page_title="AI 创作工作室", page_icon="✨", layout="centered")

custom_css = """
<style>
    /* 暴力隐藏所有开发者的丑陋标签 */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden !important;}
    footer {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden;}
    
    /* 纯黑背景 */
    .stApp {
        background-color: #0E0E0E;
        color: #E0E0E0;
    }
    
    /* 侧边栏样式 */
    [data-testid="stSidebar"] {
        background-color: #161616;
        border-right: 1px solid #333;
    }
    
    /* 优化主区域边距，让输入框更贴近底部 */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 5rem;
        max-width: 800px;
    }
    
    /* 悬浮输入框（即梦同款） */
    [data-testid="stChatInput"] {
        background-color: #1E1E1E !important;
        border: 1px solid #444 !important;
        border-radius: 20px !important;
        padding: 10px 20px !important;
        color: white !important;
        box-shadow: 0 0 15px rgba(0, 240, 255, 0.1) !important;
    }
    
    /* 去掉图片默认边框，加圆角和阴影 */
    .stImage img {
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    }
    
    /* 隐藏单选框的圆圈，变成文字按钮样式（如果不放侧边栏的话） */
    div[role="radiogroup"] > label > div:first-child {
        display: none;
    }
    div[role="radiogroup"] > label {
        background-color: #1E1E1E;
        padding: 5px 15px;
        border-radius: 15px;
        margin-right: 10px;
        border: 1px solid #333;
        cursor: pointer;
    }
    div[role="radiogroup"] > label:hover {
        border-color: #00F0FF;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

load_dotenv()
client_chat = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")

# ================= 2. 侧边栏（模式与历史） =================
with st.sidebar:
    st.markdown("<h2 style='color:white;'>✨ AI Studio</h2>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("**当前模式**")
    # 把选择器放在侧边栏，主页面保持纯净
    mode = st.radio("Mode", ["🎬 图文短剧", "🎨 单张绘图"], label_visibility="collapsed")
    
    st.markdown("---")
    st.markdown("**清空对话**")
    if st.button("新建对话 🗑️", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ================= 3. 主界面对话流 =================
st.markdown("<h2 style='text-align: center; color: white; margin-bottom: 2rem;'>✨ 让想象触手可及</h2>", unsafe_allow_html=True)

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
                    # 彻底解决警告：使用 use_container_width
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
            
            # 动态占位符，提升加载体验
            placeholder = st.empty()
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
                            pass # 忽略单张失败
            
            st.session_state.messages.append({
                "role": "assistant", "type": "image_list", "content": images_data
            })