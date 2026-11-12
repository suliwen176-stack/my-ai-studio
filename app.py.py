import streamlit as st
import os
import json
import urllib.request
import asyncio
import edge_tts
import nest_asyncio
import time
from openai import OpenAI
from dotenv import load_dotenv

# 解决 Streamlit 中不能直接使用 asyncio.run() 的问题
nest_asyncio.apply()

# ================= 1. 注入极简 CSS =================
st.set_page_config(page_title="AI 创作工作室", page_icon="✨", layout="centered")

custom_css = """
<style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    [data-testid="stToolbar"] {visibility: hidden !important;}
    [data-testid="stStatusWidget"] {visibility: hidden !important;}
    
    .stApp { background-color: #050505; color: #E0E0E0; }
    .block-container { padding-top: 3rem; padding-bottom: 6rem; max-width: 800px; }
    
    [data-testid="stChatInput"] {
        background-color: #141414 !important;
        border: 1px solid #2A2A2A !important;
        border-radius: 30px !important;
        padding: 12px 24px !important;
        color: white !important;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.8) !important;
    }
    [data-testid="stChatMessage"] { background-color: transparent !important; border: none !important; }
    .stImage img { border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.6); }
    
    div[role="radiogroup"] { display: flex; justify-content: center; margin-bottom: 2rem; }
    div[role="radiogroup"] > label > div:first-child { display: none; }
    div[role="radiogroup"] > label {
        background-color: #141414; padding: 8px 20px; border-radius: 20px; margin: 0 10px;
        border: 1px solid #2A2A2A; cursor: pointer;
    }
    div[role="radiogroup"] > label[data-checked="true"] { background-color: #FFFFFF; color: #000; }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

load_dotenv()
client_chat = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")

# ================= 2. 语音生成函数 =================
async def generate_audio(text, filename):
    voice = "zh-CN-YunxiNeural" # 云希，非常自然的情感男声
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(filename)

# ================= 3. 主界面 =================
mode = st.radio("模式切换", ["🎬 有声图文短剧", "🎨 单张绘图"], label_visibility="collapsed")

if "messages" not in st.session_state:
    st.session_state.messages = []

if not st.session_state.messages:
    st.markdown("""
        <div style='text-align: center; margin-top: 10vh; margin-bottom: 10vh;'>
            <h1 style='color: #FFFFFF; font-weight: 300; font-size: 2.5rem;'>让想象触手可及</h1>
            <p style='color: #888;'>在下方输入您的剧本，AI 将为您生成画面和配音</p>
        </div>
    """, unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["type"] == "text":
            st.markdown(msg["content"])
        elif msg["type"] == "image_list":
            cols = st.columns(3)
            for i, img in enumerate(msg["content"]):
                with cols[i % 3]:
                    st.image(img["url"], caption=img["caption"], use_container_width=True)
        elif msg["type"] == "audio":
            st.audio(msg["content"], format="audio/mp3")

user_input = st.chat_input("输入想法、剧本或画面描述，和 Agent 一起创作...")

if user_input:
    st.session_state.messages.append({"role": "user", "type": "text", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

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
                    
        elif mode == "🎬 有声图文短剧":
            with st.spinner("导演正在拆解剧本..."):
                prompt = f"""你是一个电影分镜师。将剧本拆解为分镜。严格输出JSON：
                [{{"shot_id": 1, "visual_prompt": "英文画面描述", "dialogue": "台词或旁白"}}]
                剧本：{user_input}"""
                
                try:
                    res = client_chat.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompt}])
                    clean_json = res.choices[0].message.content.replace("```json", "").replace("```", "").strip()
                    storyboard = json.loads(clean_json)
                except Exception as e:
                    st.error(f"剧本拆解失败：{e}")
                    st.stop()

            st.markdown(f"✅ 拆解完毕！共 {len(storyboard)} 个镜头，正在生成...")
            
            cols = st.columns(3)
            images_data = []
            full_narration = "" 
            
            for i, shot in enumerate(storyboard):
                with cols[i % 3]:
                    st.caption(f"镜头 {shot['shot_id']}: {shot.get('dialogue', '')}")
                    if shot.get('dialogue'):
                        full_narration += shot.get('dialogue') + "。"
                        
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
            
            # 生成配音
            if full_narration:
                st.markdown("### 🎙️ AI 配音")
                with st.spinner("正在合成沉浸式语音..."):
                    audio_file = f"tts_{int(time.time())}.mp3"
                    try:
                        # 使用 nest_asyncio 后可以安全调用
                        asyncio.run(generate_audio(full_narration, audio_file))
                        
                        with open(audio_file, "rb") as f:
                            audio_bytes = f.read()
                            st.audio(audio_bytes, format="audio/mp3")
                            st.session_state.messages.append({"role": "assistant", "type": "audio", "content": audio_bytes})
                        os.remove(audio_file)
                    except Exception as e:
                        st.error(f"配音生成失败：{e}")

            st.session_state.messages.append({
                "role": "assistant", "type": "image_list", "content": images_data
            })