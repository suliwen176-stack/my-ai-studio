import streamlit as st
import os
import json
import time
import urllib.request
from openai import OpenAI
from dotenv import load_dotenv

st.set_page_config(page_title="AI 短剧导演工作台", page_icon="🎬", layout="wide")
os.environ['PYTHONIOENCODING'] = 'utf-8'
load_dotenv()

# --- 初始化模型 ---
client_chat = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")

# --- 侧边栏 ---
with st.sidebar:
    st.title("🎬 导演工作台")
    st.info("粘贴剧本拆解分镜，或直接生成视频。")

# --- 主界面标签页 ---
tab1, tab2, tab3 = st.tabs(["📝 剧本转分镜漫剧", "🎨 单张快速绘图", "🎥 AI 视频生成"])

# ================= 功能一：剧本转漫剧 =================
with tab1:
    st.header("剧本转分镜")
    script_text = st.text_area("请粘贴一段剧本（建议先输入 3-5 句测试）：", height=150)
    
    if st.button("开始拆解并绘图", type="primary"):
        if not script_text:
            st.warning("请先输入剧本！")
        else:
            with st.status("导演正在拆解剧本...", expanded=True) as status:
                prompt = f"""你是一个电影分镜师。将以下剧本拆解为分镜。严格按照 JSON 数组格式输出：
                [{{"shot_id": 1, "visual_prompt": "英文画面描述", "dialogue": "台词"}}]
                剧本：{script_text}"""
                
                res = client_chat.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompt}])
                
                try:
                    clean_json = res.choices[0].message.content.replace("```json", "").replace("```", "").strip()
                    storyboard = json.loads(clean_json)
                    status.update(label=f"✅ 拆解完成！共 {len(storyboard)} 个镜头。", state="complete")
                except Exception as e:
                    st.error(f"剧本拆解失败，格式错误：{e}")
                    st.stop()

            st.write("---")
            st.write("### 🎬 分镜画面")
            cols = st.columns(3)
            
            for i, shot in enumerate(storyboard):
                col = cols[i % 3]
                with col:
                    st.markdown(f"**镜头 {shot['shot_id']}**")
                    st.caption(f"台词：{shot.get('dialogue', '无')}")
                    with st.spinner(f"正在绘制镜头 {shot['shot_id']}..."):
                        try:
                            api_key = os.getenv("ZHIPU_API_KEY").strip()
                            url = "https://open.bigmodel.cn/api/paas/v4/images/generations"
                            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                            payload = {"model": "cogview-3-flash", "prompt": shot['visual_prompt']}
                            
                            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
                            with urllib.request.urlopen(req) as response:
                                result = json.loads(response.read().decode('utf-8'))
                                img_url = result['data'][0]['url']
                                st.image(img_url, use_column_width=True)
                        except Exception as e:
                            st.error(f"镜头 {shot['shot_id']} 生成失败")

# ================= 功能二：单张快速绘图 =================
with tab2:
    st.header("单张快速绘图")
    prompt_single = st.text_input("请输入画面描述：", placeholder="例如：赛博朋克风格的城市...")
    
    if st.button("生成图片", type="primary", key="btn_single") and prompt_single:
        with st.spinner("正在作画..."):
            try:
                api_key = os.getenv("ZHIPU_API_KEY").strip()
                url = "https://open.bigmodel.cn/api/paas/v4/images/generations"
                headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                payload = {"model": "cogview-3-flash", "prompt": prompt_single}
                
                req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
                with urllib.request.urlopen(req) as response:
                    result = json.loads(response.read().decode('utf-8'))
                    img_url = result['data'][0]['url']
                    st.image(img_url, use_column_width=True)
            except Exception as e:
                st.error(f"生成失败：{e}")

# ================= 功能三：AI 视频生成（商业架构版） =================
with tab3:
    st.header("AI 视频生成（商业架构版）")
    
    if "video_task_id" not in st.session_state:
        st.session_state.video_task_id = None
    if "video_status" not in st.session_state:
        st.session_state.video_status = None
    if "video_url" not in st.session_state:
        st.session_state.video_url = None

    video_prompt = st.text_input("请输入视频画面描述：", placeholder="例如：古风宅院，大雪纷飞...", disabled=(st.session_state.video_task_id is not None))
    
    if st.button("1. 提交生成任务", type="primary", key="btn_submit_video") and video_prompt:
        with st.spinner("正在提交任务到云端..."):
            try:
                api_key = os.getenv("ZHIPU_API_KEY").strip()
                url = "https://open.bigmodel.cn/api/paas/v4/videos/generations"
                headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                payload = {"model": "cogvideox-flash", "prompt": video_prompt}
                
                req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
                with urllib.request.urlopen(req) as response:
                    result = json.loads(response.read().decode('utf-8'))
                    st.session_state.video_task_id = result.get("id")
                    st.session_state.video_status = "PENDING"
                    st.success(f"任务提交成功！Task ID: {st.session_state.video_task_id}")
                    st.rerun()
            except Exception as e:
                st.error(f"提交失败：{e}")

    if st.session_state.video_task_id:
        st.info(f"当前任务 ID：{st.session_state.video_task_id}")
        
        if st.button("2. 查询渲染进度", type="secondary"):
            with st.spinner("正在向云端查询..."):
                try:
                    api_key = os.getenv("ZHIPU_API_KEY").strip()
                    status_url = f"https://open.bigmodel.cn/api/paas/v4/async-result/{st.session_state.video_task_id}"
                    status_req = urllib.request.Request(status_url, headers={"Authorization": f"Bearer {api_key}"})
                    
                    with urllib.request.urlopen(status_req) as context_res:
                        status_data = json.loads(context_res.read().decode('utf-8'))
                        task_status = status_data.get("task_status")
                        st.session_state.video_status = task_status
                        
                        if task_status == "SUCCESS":
                            st.session_state.video_url = status_data["video_result"][0]["url"]
                        elif task_status == "FAIL":
                            st.error("视频生成失败了，请重试。")
                            st.session_state.video_task_id = None
                        else:
                            st.warning(f"当前状态：{task_status}，请稍后再试...")
                                except Exception as e:
                    st.error(f"查询失败：{e}")

        if st.session_state.video_status == "SUCCESS" and st.session_state.video_url:
            st.success("🎉 视频渲染完成！")
            st.video(st.session_state.video_url)
            
            if st.button("生成下一个视频"):
                st.session_state.video_task_id = None
                st.session_state.video_status = None
                st.session_state.video_url = None
                st.rerun()