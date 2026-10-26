# 1. 定义我们的“处理机器”（函数）
# 这个函数接收一个金额，自动判断它的状态并返回结果
def check_expense(amount):
    if amount < 0:
        return "警告：数据异常（负数）"
    elif amount > 5000:
        return "高额费用"
    else:
        return "常规费用"

# 2. 准备一批数据（列表 List）
# 这里包含了 5 笔费用，其中有一笔是负数
expense_list = [800, 9000, 4500, 2500, -500, 10000]


print("开始批量处理研发费用...")

# 3. 用 for 循环遍历这些数据
for money in expense_list:
    # 调用我们的机器，把 money 传进去，并把结果接住
    result = check_expense(money)
    
    # 打印出来
    print(f"金额：{money}，检查结果：{result}")

print("批量处理结束！")