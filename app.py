
import streamlit as st
import os
import json
import re
import urllib.request
import urllib.error
import asyncio
import time
import tempfile

import edge_tts
import dashscope

from openai import OpenAI
from dotenv import load_dotenv


# =====================================================
# 1. 页面配置
# =====================================================

st.set_page_config(
    page_title="AI 创作工作室",
    page_icon="✨",
    layout="centered"
)

load_dotenv()


def get_config(name, default=None):
    """优先读取 Streamlit Secrets，其次读取环境变量。"""
    try:
        value = st.secrets.get(name, None)
        if value:
            return value
    except Exception:
        pass

    return os.getenv(name, default)


custom_css = """
<style>
#MainMenu {visibility: hidden;}
header {visibility: hidden !important;}
footer {visibility: hidden !important;}
[data-testid="stToolbar"] {visibility: hidden !important;}
[data-testid="stStatusWidget"] {visibility: hidden !important;}

.stApp {
    background-color: #050505;
    color: #E0E0E0;
}

.block-container {
    padding-top: 3rem;
    padding-bottom: 6rem;
    max-width: 900px;
}

[data-testid="stChatInput"] {
    background-color: #141414 !important;
    border: 1px solid #2A2A2A !important;
    border-radius: 30px !important;
    padding: 12px 24px !important;
    color: white !important;
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.8) !important;
}

[data-testid="stChatMessage"] {
    background-color: transparent !important;
    border: none !important;
}

.stImage img {
    border-radius: 12px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.6);
}

div[role="radiogroup"] {
    display: flex;
    justify-content: center;
    margin-bottom: 2rem;
}

div[role="radiogroup"] > label > div:first-child {
    display: none;
}

div[role="radiogroup"] > label {
    background-color: #141414;
    padding: 8px 20px;
    border-radius: 20px;
    margin: 0 10px;
    border: 1px solid #2A2A2A;
    cursor: pointer;
}
</style>
"""

st.markdown(custom_css, unsafe_allow_html=True)


# =====================================================
# 2. API 配置
# =====================================================

DEEPSEEK_API_KEY = get_config("DEEPSEEK_API_KEY")
ZHIPU_API_KEY = get_config("ZHIPU_API_KEY")
DASHSCOPE_API_KEY = get_config("DASHSCOPE_API_KEY")

DASHSCOPE_WORKSPACE_ID = get_config("DASHSCOPE_WORKSPACE_ID")
DASHSCOPE_REGION = get_config("DASHSCOPE_REGION", "cn-beijing")


def get_chat_client():
    if not DEEPSEEK_API_KEY:
        raise ValueError("缺少 DEEPSEEK_API_KEY，请检查 Secrets。")

    return OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com"
    )


def get_video_client():
    if not DASHSCOPE_API_KEY:
        raise ValueError("缺少 DASHSCOPE_API_KEY，请检查 Secrets。")

    if not DASHSCOPE_WORKSPACE_ID:
        raise ValueError(
            "缺少 DASHSCOPE_WORKSPACE_ID，请在 Secrets 中配置百炼业务空间 ID。"
        )

    return dashscope.Client(
        api_key=DASHSCOPE_API_KEY,
        workspace=DASHSCOPE_WORKSPACE_ID,
        region=DASHSCOPE_REGION
    )


# =====================================================
# 3. 初始化会话状态
# =====================================================

defaults = {
    "messages": [],
    "storyboard_images": [],
    "video_results": {},
    "current_storyboard_id": None,
    "is_processing": False
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =====================================================
# 4. 智谱图片生成
# =====================================================

def generate_image(prompt):

    if not ZHIPU_API_KEY:
        raise ValueError("缺少 ZHIPU_API_KEY，请检查 Secrets。")

    url = "https://open.bigmodel.cn/api/paas/v4/images/generations"

    headers = {
        "Authorization": f"Bearer {ZHIPU_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "cogview-3-flash",
        "prompt": prompt
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=180) as response:
        result = json.loads(
            response.read().decode("utf-8")
        )

    if not result.get("data"):
        raise RuntimeError(f"图片 API 没有返回图片：{result}")

    return result["data"][0]["url"]


# =====================================================
# 5. DeepSeek 剧本拆解
# =====================================================

def extract_json(text):

    text = text.strip()

    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(r"\s*```$", "", text)

    start = text.find("[")
    end = text.rfind("]")

    if start == -1 or end == -1:
        raise ValueError("AI 没有返回有效的 JSON 数组。")

    return json.loads(text[start:end + 1])


def generate_storyboard(user_input):

    client = get_chat_client()

    prompt = f"""
你是一名专业电影导演、编剧和分镜师。

请将用户提供的故事拆解为适合 AI 图片生成和图生视频的分镜。

要求：

1. 根据剧情合理拆分镜头，建议3-6个镜头。
2. 每个镜头必须推动剧情，不要重复相同画面。
3. 所有镜头保持人物外貌、服装、年龄、发型的一致性。
4. visual_prompt 必须使用英文，描述静态画面的构图、人物、环境、光线和电影质感。
5. video_prompt 必须使用英文，描述人物动作、环境运动、镜头移动和动态效果。
6. 不要让人物在不同镜头中突然改变服装或外貌。
7. dialogue 使用自然中文台词或旁白。
8. 不要添加剧本中不存在的重要人物或事件。

严格返回 JSON 数组，不要输出其他解释。

格式：

[
  {{
    "shot_id": 1,
    "visual_prompt": "Detailed English cinematic image description",
    "video_prompt": "Detailed English motion and camera movement description",
    "dialogue": "中文旁白或人物台词"
  }}
]

用户剧本：
{user_input}
"""

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.8
    )

    content = response.choices[0].message.content

    storyboard = extract_json(content)

    if not isinstance(storyboard, list) or not storyboard:
        raise ValueError("没有生成有效分镜。")

    # 限制单次剧本的镜头数量，控制生成成本
    storyboard = storyboard[:6]

    return storyboard


# =====================================================
# 6. Edge TTS 配音
# =====================================================

def generate_tts(text):

    async def _generate():
        communicate = edge_tts.Communicate(
            text,
            "zh-CN-YunxiNeural"
        )

        audio_data = bytearray()

        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data.extend(chunk["data"])

        return bytes(audio_data)

    return asyncio.run(_generate())


# =====================================================
# 7. 万相图生视频
# =====================================================

def generate_video(image_url, video_prompt):

    client = get_video_client()

    # 同步调用：SDK 自动提交任务并等待完成
    job = client.videos.generate(
        model="wan2.6-i2v-flash",
        prompt=video_prompt,
        image_url=image_url,
        resolution="720P",
        duration=5,
        prompt_extend=True,
        watermark=True
    )

    video_url = getattr(job, "video_url", None)

    if not video_url:
        raise RuntimeError(
            f"万相没有返回视频地址，任务结果：{job}"
        )

    return video_url


# =====================================================
# 8. 页面标题和模式切换
# =====================================================

st.markdown(
    "<h1 style='text-align:center;'>✨ AI 创作工作室</h1>",
    unsafe_allow_html=True
)

st.caption(
    "让创意变成画面，让画面拥有声音和生命。"
)

mode = st.radio(
    "模式切换",
    ["🎬 有声图文短剧", "🎨 单张绘图"],
    horizontal=True,
    label_visibility="collapsed"
)
# ================= 视频上传与播放 =================
uploaded_video = st.file_uploader("请选择你生成的 MP4 视频文件", type=["mp4", "mov", "avi"])
if uploaded_video is not None:
    st.video(uploaded_video)

# =====================================================
# 9. 渲染历史消息
# =====================================================

for msg in st.session_state.messages:

    with st.chat_message(msg["role"]):

        if msg["type"] == "text":
            st.markdown(msg["content"])

        elif msg["type"] == "image_list":

            cols = st.columns(3)

            for i, img in enumerate(msg["content"]):
                with cols[i % 3]:
                    st.image(
                        img["url"],
                        caption=img["caption"],
                        use_container_width=True
                    )

        elif msg["type"] == "audio":

            st.audio(
                msg["content"],
                format="audio/mp3"
            )

        elif msg["type"] == "video":

            st.video(msg["content"])


# =====================================================
# 10. 用户输入
# =====================================================

user_input = st.chat_input(
    "输入想法、剧本或画面描述，和 Agent 一起创作..."
)


if user_input:

    st.session_state.messages.append({
        "role": "user",
        "type": "text",
        "content": user_input
    })

    try:

        # -------------------------------------------------
        # 模式 A：单张绘图
        # -------------------------------------------------

        if mode == "🎨 单张绘图":

            with st.spinner("AI 正在绘制画面..."):

                img_url = generate_image(user_input)

            st.session_state.messages.append({
                "role": "assistant",
                "type": "image_list",
                "content": [
                    {
                        "url": img_url,
                        "caption": user_input
                    }
                ]
            })


        # -------------------------------------------------
        # 模式 B：有声图文短剧
        # -------------------------------------------------

        elif mode == "🎬 有声图文短剧":

            with st.spinner("导演正在拆解剧本..."):

                storyboard = generate_storyboard(user_input)

            images_data = []
            full_narration = ""

            progress = st.progress(0)

            status = st.empty()

            for i, shot in enumerate(storyboard):

                status.write(
                    f"正在绘制镜头 {i + 1}/{len(storyboard)}..."
                )

                try:

                    img_url = generate_image(
                        shot["visual_prompt"]
                    )

                    images_data.append({
                        "shot_id": shot["shot_id"],
                        "url": img_url,
                        "caption": shot.get("dialogue", ""),
                        "visual_prompt": shot["visual_prompt"],
                        "video_prompt": shot.get(
                            "video_prompt",
                            shot["visual_prompt"]
                        )
                    })

                    if shot.get("dialogue"):
                        full_narration += (
                            shot["dialogue"] + "。"
                        )

                except Exception as e:

                    st.warning(
                        f"镜头 {shot['shot_id']} 图片生成失败：{e}"
                    )

                progress.progress(
                    (i + 1) / len(storyboard)
                )

            status.empty()
            progress.empty()

            if not images_data:
                raise RuntimeError("所有分镜图片均生成失败。")

            # 保存分镜数据，保证按钮点击后不会丢失
            st.session_state.storyboard_images = images_data

            st.session_state.video_results = {}

            st.session_state.current_storyboard_id = (
                str(time.time())
            )

            st.session_state.messages.append({
                "role": "assistant",
                "type": "text",
                "content": (
                    f"✅ 剧本拆解完成！共 {len(storyboard)} 个镜头。"
                    f"\n\n成功生成 {len(images_data)} 张分镜图片。"
                    "\n\n你可以在下方选择需要转换成视频的镜头。"
                )
            })

            # 生成旁白
            if full_narration.strip():

                with st.spinner("正在生成 AI 中文配音..."):

                    audio_bytes = generate_tts(
                        full_narration
                    )

                if audio_bytes:

                    st.session_state.messages.append({
                        "role": "assistant",
                        "type": "audio",
                        "content": audio_bytes
                    })

    except Exception as e:

        st.session_state.messages.append({
            "role": "assistant",
            "type": "text",
            "content": f"❌ 创作失败：{str(e)}"
        })

    # 重新渲染页面，确保新生成的数据正常显示
    st.rerun()


# =====================================================
# 11. 分镜展示及独立视频生成
# =====================================================

if st.session_state.storyboard_images:

    st.markdown("---")

    st.markdown("## 🎞️ 我的分镜")

    st.caption(
        "选择一个镜头，点击按钮，即可使用万相生成动态视频。"
    )

    for i, shot in enumerate(
        st.session_state.storyboard_images
    ):

        with st.container(border=True):

            st.markdown(
                f"### 镜头 {shot['shot_id']}"
            )

            st.image(
                shot["url"],
                use_container_width=True
            )

            if shot.get("caption"):
                st.write(
                    f"**剧情台词：** {shot['caption']}"
                )

            st.caption(
                f"动态描述：{shot['video_prompt']}"
            )

            video_key = str(shot["shot_id"])

            # 这里的按钮不再依赖 user_input
            # Streamlit 页面重新运行后仍然能够触发

            if st.button(
                f"🎬 让镜头 {shot['shot_id']} 动起来",
                key=f"video_button_{i}",
                use_container_width=True
            ):

                try:

                    with st.spinner(
                        "万相正在生成视频，通常需要1-5分钟，请不要关闭页面..."
                    ):

                        video_url = generate_video(
                            shot["url"],
                            shot["video_prompt"]
                        )

                    st.session_state.video_results[
                        video_key
                    ] = video_url

                    st.success(
                        f"🎉 镜头 {shot['shot_id']} 视频生成成功！"
                    )

                except Exception as e:

                    st.error(
                        f"视频生成失败：{str(e)}"
                    )

            # 显示已经生成的视频

            if video_key in st.session_state.video_results:

                st.markdown("#### 🎥 视频预览")

                st.video(
                    st.session_state.video_results[video_key]
                )


# =====================================================
# 12. 页面底部
# =====================================================

st.markdown("---")

st.caption(
    "AI 创作工作室 | DeepSeek + CogView + Wan 2.6 + Edge TTS"
)
