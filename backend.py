from fastapi import FastAPI
import os
import json
import urllib.request
import ssl
import asyncio
import threading
import edge_tts
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

app = FastAPI()

# ================= 0. 基础测试接口 =================
@app.get("/")
def read_root():
    return {"message": "欢迎来到我的 AI 后端！"}

@app.get("/api/hello/{name}")
def say_hello(name: str):
    return {"reply": f"你好，{name}！你的后端跑通了！"}

# ================= 1. 文生图接口 (智谱) =================
@app.get("/api/draw/{prompt}")
def generate_image(prompt: str):
    try:
        api_key = os.getenv("ZHIPU_API_KEY")
        if not api_key:
            return {"status": "error", "message": "请在 .env 中配置 ZHIPU_API_KEY"}
            
        url = "https://open.bigmodel.cn/api/paas/v4/images/generations"
        headers = {"Authorization": f"Bearer {api_key.strip()}", "Content-Type": "application/json"}
        payload = {
            "model": "cogview-3-flash", 
            "prompt": prompt
        }
        
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
        
        # 绕过本地 Mac 的证书验证问题
        context = ssl._create_unverified_context()
        with urllib.request.urlopen(req, context=context) as response:
            result = json.loads(response.read().decode('utf-8'))
            img_url = result['data'][0]['url']
            return {"status": "success", "prompt": prompt, "image_url": img_url}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ================= 2. 语音合成接口 (Edge-TTS) =================
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

@app.get("/api/tts/{text}")
def generate_audio(text: str):
    audio_file = "temp_audio.mp3"
    try:
        run_tts_in_thread(text, audio_file)
        return {"status": "success", "message": "音频已生成", "file": audio_file}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ================= 3. 提交图生视频任务 (阿里云) =================
@app.get("/api/video")
def generate_video(prompt: str, image_url: str):
    try:
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            return {"status": "error", "message": "请在 .env 中配置 DASHSCOPE_API_KEY"}
            
        url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis"
        
        headers = {
            "Authorization": f"Bearer {api_key.strip()}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable"
        }
        
        payload = {
            "model": "wan2.6-i2v-flash",
            "input": {
                "prompt": prompt,
                "img_url": image_url
            },
            "parameters": {
                "resolution": "720P",
                "duration": 5,
                "prompt_extend": True
            }
        }
        
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status() 
        
        result = response.json()
        # 返回结果里会包含 task_id
        return {"status": "success", "message": "任务已提交", "task_info": result}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ================= 4. 查询视频生成进度 (阿里云) =================
@app.get("/api/video/status/{task_id}")
def check_video_status(task_id: str):
    try:
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            return {"status": "error", "message": "请在 .env 中配置 DASHSCOPE_API_KEY"}
            
        # 注意这里：用 task_id 拼接到 URL 后面
        url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
        
        headers = {
            "Authorization": f"Bearer {api_key.strip()}"
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        return {"status": "success", "task_info": result}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}
        import os

# ================= 5. 一键下载视频接口 =================
@app.get("/api/video/download/{task_id}")
def download_video(task_id: str):
    try:
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            return {"status": "error", "message": "请在 .env 中配置 DASHSCOPE_API_KEY"}
            
        # 1. 查询任务状态，获取最新的视频链接
        status_url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
        headers = {"Authorization": f"Bearer {api_key.strip()}"}
        
        res = requests.get(status_url, headers=headers)
        res.raise_for_status()
        result = res.json()
        
        if result.get("output", {}).get("task_status") != "SUCCEEDED":
            return {"status": "error", "message": "视频还没生成好，请稍后刷新重试"}
            
        video_url = result["output"]["video_url"]
        
        # 2. 直接下载视频并保存到本地
        print(f"正在下载视频: {video_url}")
        video_res = requests.get(video_url, stream=True)
        video_res.raise_for_status()
        
        file_name = f"video_{task_id}.mp4"
        with open(file_name, "wb") as f:
            for chunk in video_res.iter_content(chunk_size=8192):
                f.write(chunk)
                
        return {"status": "success", "message": f"视频已成功下载到后端目录，文件名为：{file_name}"}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}