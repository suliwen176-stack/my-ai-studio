# ================= 功能三：AI 视频生成（真实异步版） =================
import time # 确保文件顶部有 import time

with tab3:
    st.header("AI 视频生成（商业架构版）")
    
    # 1. 初始化记忆状态（用于跨次刷新保存 task_id）
    if "video_task_id" not in st.session_state:
        st.session_state.video_task_id = None
    if "video_status" not in st.session_state:
        st.session_state.video_status = None
    if "video_url" not in st.session_state:
        st.session_state.video_url = None

    # 2. 输入区和提交按钮
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
                    st.rerun() # 刷新页面，更新UI状态
            except Exception as e:
                st.error(f"提交失败：{e}")

    # 3. 状态轮询与结果展示区
    if st.session_state.video_task_id:
        st.info(f"当前任务 ID：{st.session_state.video_task_id}")
        
        # 手动查询按钮（替代死循环，防止网页卡死）
        if st.button("2. 查询渲染进度", type="secondary"):
            with st.spinner("正在向云端查询..."):
                try:
                    api_key = os.getenv("ZHIPU_API_KEY").strip()
                    status_url = f"https://open.bigmodel.cn/api/paas/v4/async-result/{st.session_state.video_task_id}"
                    status_req = urllib.request.Request(status_url, headers={"Authorization": f"Bearer {api_key}"})
                    
                    with urllib.request.urlopen(status_req) as status_res:
                        status_data = json.loads(status_res.read().decode('utf-8'))
                        task_status = status_data.get("task_status")
                        st.session_state.video_status = task_status
                        
                        if task_status == "SUCCESS":
                            st.session_state.video_url = status_data["video_result"][0]["url"]
                        elif task_status == "FAIL":
                            st.error("视频生成失败了，请重试。")
                            st.session_state.video_task_id = None # 重置
                        else:
                            st.warning(f"当前状态：{task_status}，请稍后再试...")
                except Exception as e:
                    st.error(f"查询失败：{e}")

        # 如果成功了，显示视频并提供重置按钮
        if st.session_state.video_status == "SUCCESS" and st.session_state.video_url:
            st.success("🎉 视频渲染完成！")
            st.video(st.session_state.video_url)
            
            if st.button("生成下一个视频"):
                st.session_state.video_task_id = None
                st.session_state.video_status = None
                st.session_state.video_url = None
                st.rerun()