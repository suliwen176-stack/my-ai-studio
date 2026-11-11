import streamlit as st
import os
import json
import urllib.request
from openai import OpenAI
from dotenv import load_dotenv

# ================= 1. 注入即梦风 CSS =================
st.set_page_config(page_title="AI 创作工作台", page_icon="✨", layout="wide")

# 隐藏默认的菜单、页眉、页脚，并设置纯黑背景和极简输入框
custom_css = """
<style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 整体背景纯黑 */
    .stApp {
        background-color: #000000;
        color: #E0E0E0;
    }
    
    /* 侧边栏颜色 */
    [data-testid="stSidebar"] {
        background-color: #111111;
        border-right: 1px solid #333;
    }
    
    /* 悬浮输入框美化（像即梦底部那样） */
    [data-testid="stChatInput"] {
        background-color: #1E1E1E !important;
        border: 1px solid #444 !important;
        border-radius: 25px !important;
        padding: 10px 20px !important;
        color: white !important;
    }
    
    /* 对话气泡美化 */
    [data-testid="stChatMessage"] {
        background-color: transparent !important;
        padding: 10px 0 !important;
    }
    
    /* 去掉图片的默认外框 */
    .stImage img {
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        transition: transform 0.3s ease;
    }
    .stImage img:hover {
        transform: scale(1.02);
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

load_dotenv()
client_chat = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")

# ================= 2. 侧边栏（极简控制台） =================
with st.sidebar:
    st.markdown("<h2 style='color:white;'>✨ AI Studio</h2>", unsafe_allow_html=True)
    st.caption("像即梦一样创作")
    st.markdown("---")
    # 把之前的“三个功能”变成侧边栏的模式选择
    mode = st.radio("选择创作模式", ["🎬 图文短剧", "🎨 单张绘图"], label_visibility="collapsed")
    st.markdown("---")
    st.info("💡 提示：输入剧本或画面描述，AI 会自动帮你拆解并生成。")
    st.caption("v2.0 即梦风")

# ================= 3. 主界面对话区 =================
# 初始化聊天记录
if "messages" not in st.session_state:
    st.session_state.messages = []

# 每次刷新时，先渲染历史记录
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["type"] == "text":
            st.markdown(msg["content"])
        elif msg["type"] == "image_list":
            cols = st.columns(3)
            for i, img in enumerate(msg["content"]):
                with cols[i % 3]:
                    st.image(img["url"], caption=img["caption"], use_container_width=True)

# 底部悬浮输入框（即梦同款）
user_input = st.chat_input("输入想法、剧本或画面描述，和 Agent 一起创作...")

if user_input:
    # 1. 显示用户输入
    st.session_state.messages.append({"role": "user", "type": "text", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 2. AI 开始工作
    with st.chat_message("assistant"):
        if mode == "🎨 单张绘图":
            with st.spinner("正在绘制中..."):
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
                        
                        # 存入记忆
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

            st.markdown(f"✅ 剧本拆解完毕！共 {len(storyboard)} 个镜头。正在生成画面...")
            
            # 由于即梦是流式返回，我们这里用占位符动态显示图片
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
                            st.error("某镜头绘制失败")
            
            # 存入记忆
            st.session_state.messages.append({
                "role": "assistant", "type": "image_list", "content": images_data
            })