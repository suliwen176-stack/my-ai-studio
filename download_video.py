import requests

# 你生成的视频链接
url = "https://dashscope-a717.oss-accelerate.aliyuncs.com/1d/05/20261113/87ff3641/a5b5fb9eefc049b387e3dc759b988071-metadata_4b3f2d9ffcb92cb1.mp4?Expires=1794600778&OSSAccessKeyId=LTAI5tJj66wshad1Sf7iezX4&Signature=3wcwJLtoM0za4X1czK2GMTw0ET4%3D"

print("正在下载视频，请稍候...")
try:
    # 使用 requests 正确发起 GET 请求，避免浏览器对 URL 的错误处理
    response = requests.get(url, stream=True)
    response.raise_for_status()  # 如果请求失败会抛出异常

    # 将视频内容分块写入文件，适合大文件下载
    with open("my_first_ai_video.mp4", "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print("🎉 下载成功！文件名为：my_first_ai_video.mp4")
except Exception as e:
    print(f"下载失败：{e}")