import os
import json
import time
import urllib.request
import ssl  # 【新增】引入 ssl 模块
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("ZHIPU_API_KEY").strip()

# 【新增】创建一个不验证证书的上下文（仅限本地测试使用）
context = ssl._create_unverified_context()

# 1. 提交视频生成任务
url = "https://open.bigmodel.cn/api/paas/v4/videos/generations"
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
payload = {
    "model": "cogvideox-flash", # 智谱的免费视频模型
    "prompt": "古风宅院，大雪纷飞，一个穿着狐裘的清冷少爷坐在廊下看书，电影质感"
}

req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
print("正在提交视频生成任务...")

# 【修改】在 urlopen 中加入 context 参数
with urllib.request.urlopen(req, context=context) as response:
    result = json.loads(response.read().decode('utf-8'))
    task_id = result.get("id")
    print(f"任务提交成功！Task ID: {task_id}")
    print("等待视频渲染（大概需要 1-3 分钟）...")

# 2. 轮询任务状态
while True:
    time.sleep(10) # 每 10 秒去问一次服务器
    
    status_url = f"https://open.bigmodel.cn/api/paas/v4/async-result/{task_id}"
    status_req = urllib.request.Request(status_url, headers={"Authorization": f"Bearer {api_key}"})
    
    # 【修改】这里的 urlopen 也要加入 context 参数
    with urllib.request.urlopen(status_req, context=context) as status_res:
        status_data = json.loads(status_res.read().decode('utf-8'))
        status = status_data.get("task_status")
        
        if status == "SUCCESS":
            video_url = status_data["video_result"][0]["url"]
            print(f"\n🎉 视频生成成功！\n视频链接：{video_url}")
            break
        elif status == "FAIL":
            print(f"\n❌ 视频生成失败：{status_data}")
            break
        else:
            print(f"正在渲染中... 当前状态: {status}")