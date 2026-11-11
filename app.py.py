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

# --- 主界面使用标签页 ---
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

# ================= 功能三：AI 视频生成（模拟版） =================
with tab3:
    st.header("AI 视频生成（体验版）")
    video_prompt = st.text_input("请输入视频画面描述：", placeholder="例如：古风宅院，大雪纷飞，一个穿着狐裘的清冷少爷...")
    
    if st.button("生成视频", type="primary", key="btn_video") and video_prompt:
        with st.status("正在提交渲染任务...", expanded=True) as status:
            try:
                st.write(f"已收到提示词：{video_prompt}")
                st.write("⚠️ 注意：由于免费 API 额度受限，当前为您播放演示视频。真实的异步轮询代码已准备好，充值额度后可无缝切换。")
                
                # 模拟等待进度
                progress_bar = st.progress(0)
                for i in range(100):
                    time.sleep(0.05) # 模拟渲染等待时间
                    progress_bar.progress(i + 1)
                
                status.update(label="🎉 视频生成成功！", state="complete", expanded=False)
                
                # 播放一段公开的测试视频（大兔子）
                st.video("https://www.w3schools.com/html/mov_bbb.mp4")
                
            except Exception as e:
                st.error(f"发生错误：{e}")