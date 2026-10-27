import pandas as pd

# 1. 读取 Excel 文件
print("正在读取数据...")
df = pd.read_excel("expense_data.xlsx")

# 2. 初步体检：看行数、列名
print(f"数据总行数：{len(df)}")
print(f"包含的列：{list(df.columns)}")

# 3. 检查缺失字段 (isnull)
missing_count = df["金额"].isnull().sum()
print(f"发现金额缺失的行数：{missing_count}")

# 4. 检查重复记录 (duplicated)
duplicate_count = df.duplicated().sum()
print(f"发现完全重复的记录数：{duplicate_count}")
print("\n正在检查金额格式...")

# 5. 把金额这列强制转成数字。如果遇到转不了的（比如"三千"），就变成空值（NaN）
df["金额_纯数字"] = pd.to_numeric(df["金额"], errors="coerce")

# 找出格式错误的行（原本不是空，但转数字后变成了空）
format_error_count = df["金额_纯数字"].isnull().sum() - missing_count
print(f"发现金额格式异常的行数：{format_error_count}")

# 6. 把所有有问题的数据（缺失、格式错、重复）筛选出来
# 条件1：金额是空值（包含原本是None，和格式错误的"三千"）
condition1 = df["金额_纯数字"].isnull()

# 条件2：是完全重复的行
condition2 = df.duplicated()

# 组合条件：只要满足上面任意一个，就抓出来
abnormal_df = df[condition1 | condition2]

# 7. 把抓出来的异常清单，导出为一个新的 Excel
abnormal_df.to_excel("abnormal_list.xlsx", index=False)
print("异常清单已导出：abnormal_list.xlsx")