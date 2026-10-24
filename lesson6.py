costs = [250000, -500, 30000]

for cost in costs:
    if cost < 0:
        print("发现异常金额：", cost)
    else:
        print("金额正常：", cost)
