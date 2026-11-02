import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# 1. 定义我们要提供给 AI 的工具（Python 函数）
def calculator(a, b):
    """这是一个简单的加法计算器"""
    return a + b

# 2. 告诉 AI 我们有哪些工具（用 JSON 格式描述）
tools = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "计算两个数字的和",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "第一个数字"},
                    "b": {"type": "number", "description": "第二个数字"}
                },
                "required": ["a", "b"]
            }
        }
    }
]

print("🤖 Agent 已启动，请问有什么可以帮您？\n")
question = "帮我算一下 1250 加 3500 等于多少？"
print(f"👤 你问：{question}")

# 3. 第一轮：把问题发给 AI，并告诉它我们有工具
messages = [{"role": "user", "content": question}]
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=messages,
    tools=tools
)

message = response.choices[0].message

# 4. 核心判断：AI 是想直接回答，还是想调用工具？
if message.tool_calls:
    print("\n⚠️ AI 发现需要调用工具！")
    tool_call = message.tool_calls[0]
    function_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)
    
    print(f"🔧 AI 决定调用函数：{function_name}，参数：{arguments}")
    
    # 5. 根据 AI 的要求，在本地执行 Python 代码
    if function_name == "calculator":
        result = calculator(arguments["a"], arguments["b"])
        print(f"🧮 本地计算完成，结果是：{result}")
        
        # 6. 把 AI 刚才的“调用请求”和“计算结果”都加进历史记录
        messages.append(message) 
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": str(result)
        })
        
        # 7. 第二轮：把结果交还给 AI，让它生成最终回答
        final_response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages
        )
        print(f"\n💡 AI 最终回答：\n{final_response.choices[0].message.content}")
else:
    print(f"\n💡 AI 直接回答：\n{message.content}")