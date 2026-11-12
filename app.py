import streamlit as st
import os
import json
import urllib.request
import asyncio
import threading
import edge_tts
import time
import dashscope
from openai import OpenAI
from dotenv import load_dotenv

# ================= 1. 页面配置与 CSS 注入 =================
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

# ================= 2. 初始化模型 =================
load_dotenv()
client_chat = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

# ================= 3. 多线程 TTS 函数 (防止云端报错) =================
def run_tts_in_thread(text, filename):
    def target():
        async def _generate():
            voice = "zh-CN-YunxiNeural"
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(filename)
        asyncio.run(_generate())
    
    thread = threading.Thread(target=target)
    thread.start()
    thread.join()

# ================= 4. 主界面逻辑 =================
mode = st.radio("模式切换", ["🎬 有声图文短剧", "🎨 单张绘图"], label_visibility="collapsed")

if "messages" not in st.session_state:
    st.session_state.messages = []

# 渲染历史对话
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
        elif msg["type"] == "video":
            st.video(msg["content"])

# 底部输入框
user_input = st.chat_input("输入想法、剧本或画面描述，和 Agent 一起创作...")

if user_input:
    st.session_state.messages.append({"role": "user", "type": "text", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        # --- 模式 1：单张绘图 ---
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
                        st.session_state.messages.append({"role": "assistant", "type": "image_list", "content": [{"url": img_url, "caption": user_input}]})
                except Exception as e:
                    st.error(f"生成失败：{e}")
                    
        # --- 模式 2：有声图文短剧 ---
        elif mode == "🎬 有声图文短剧":
            with st.spinner("导演正在拆解剧本..."):
                prompt = f"""你是一个电影分镜师。将剧本拆解为分镜。严格输出JSON数组：
                [{{"shot_id": 1, "visual_prompt": "英文画面描述", "dialogue": "台词或旁白"}}]
                剧本：{user_input}"""
                try:
                    res = client_chat.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompt}])
                    clean_json = res.choices[0].message.content.replace("```json", "").replace("```", "").strip()
                    storyboard = json.loads(clean_json)
                except Exception as e:
                    st.error(f"剧本拆解失败：{e}")
                    st.stop()

            st.markdown(f"✅ 拆解完毕！共 {len(storyboard)} 个镜头。")
            
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
                                
                                st.markdown("---")
                                # 【图生视频按钮】
                                if st.button(f"🎬 让镜头 {shot['shot_id']} 动起来", key=f"video_{i}", use_container_width=True):
                                    with st.spinner("视频生成中（约1-5分钟）..."):
                                        try:
                                            job = dashscope.videos.generate(
                                                model='wan2.6-i2v-flash',
                                                prompt=shot['visual_prompt'],
                                                image_url=img_url,
                                                resolution="720P",
                                                duration=5,
                                                prompt_extend=True,
                                            )
                                            if job.video_url:
                                                st.video(job.video_url)
                                                st.session_state.messages.append({"role": "assistant", "type": "video", "content": job.video_url})
                                                st.success("🎉 视频生成成功！")
                                            else:
                                                st.error(f"生成失败：{job}")
                                        except Exception as e:
                                            st.error(f"视频生成失败：{e}")
                        except Exception as e:
                            st.error(f"镜头 {shot['shot_id']} 处理失败：{e}")
            
            # 配音生成
            if full_narration:
                st.markdown("### 🎙️ AI 配音")
                with st.spinner("正在合成沉浸式语音..."):
                    audio_file = f"tts_{int(time.time())}.mp3"
                    try:
                        run_tts_in_thread(full_narration, audio_file)
                        with open(audio_file, "rb") as f:
                            audio_bytes = f.read()
                            st.audio(audio_bytes, format="audio/mp3")
                            st.session_state.messages.append({"role": "assistant", "type": "audio", "content": audio_bytes})
                        os.remove(audio_file)
                    except Exception as e:
                        st.error(f"配音生成失败：{e}")
            
            st.session_state.messages.append({"role": "assistant", "type": "image_list", "content": images_data})