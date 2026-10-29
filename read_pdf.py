from pypdf import PdfReader

# 1. 打开 PDF 文件
pdf_path = "test.pdf"  # 换成你准备的PDF文件名
print(f"正在读取文件：{pdf_path}...")
reader = PdfReader(pdf_path)

# 2. 提取所有页面的文字，拼在一起
full_text = ""
for page in reader.pages:
    text = page.extract_text()
    if text:
        full_text += text + "\n"

print(f"✅ 读取成功！总共提取了 {len(full_text)} 个字符。\n")

# 3. 将长文本切块（Chunking）
# 假设我们每 500 个字切一块
chunk_size = 500
chunks = []

for i in range(0, len(full_text), chunk_size):
    chunk = full_text[i:i + chunk_size]
    chunks.append(chunk)

print(f"✅ 切块完成！共切成了 {len(chunks)} 块。\n")

# 4. 我们来看看第一块长什么样
print("--- 第一块的内容预览 ---")
print(chunks[0])