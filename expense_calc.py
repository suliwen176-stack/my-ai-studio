salary = -1200
material = 3500
depreciation = 2000
other = 1500

total = salary + material + depreciation + other
print("研发费用总计：", total)

error_count = 0

if salary < 0:
	error_count = error_count + 1
elif material < 0:
	error_count = error_count + 1
elif depreciation < 0:
	error_count = error_count + 1
elif other < 0:
	error_count = error_count + 1

if error_count > 0:
	print("警告：数据中存在负数，请检查！")
elif total > 8000:
	print("分类结果：高额研发费用项目")
elif total > 5000:
	print("分类结果：中等研发费用项目")
else:
	print("分类结果：常规研发费用项目")
