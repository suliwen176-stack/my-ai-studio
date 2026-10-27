import pandas as pd

# 准备一份故意搞错的数据（字典格式）
data = {
    "费用项目": ["研发人员工资", "研发材料", "研发设备折旧", "研发人员工资", "其他费用", "测试费"],
    "金额": [1200, 3500, 2000, 1200, None, "三千"], # 里面有缺失值 None，还有格式错误 "三千"
    "部门": ["研发部", "研发部", "研发部", "研发部", "行政部", "研发部"]
}

# 转换成 DataFrame 表格，并导出为 Excel
df = pd.DataFrame(data)
df.to_excel("expense_data.xlsx", index=False)
print("测试文件 expense_data.xlsx 生成成功！")