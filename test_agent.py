print("=== AI 助手已启动 ===")

# 这次我们不用文字了，直接给它两个数字
num1 = int(input("请输入第一个数字："))

print("用户问：帮我算一下", num1, "加", num2, "等于多少？")

if num1 > 0:
    print("🤖 AI 思考：数字是正数，我调用加法工具！")
    result = num1 + num2
    print("计算结果是：", result)
else:
    print("🤖 AI 思考：数字不对，我不算。")