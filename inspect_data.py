import pandas as pd
from pathlib import Path

# ---------------------------------------------------------
# CHANGE THIS if your file has a different name
# ---------------------------------------------------------
FILE_NAME = "sic_mobile_spec_PJ1.xlsx"

# Find the Excel file in the same folder as this script
file_path = Path(__file__).parent / FILE_NAME

# Check that the file exists before trying to load it
if not file_path.exists():
    print(f"ERROR: Could not find '{FILE_NAME}' in:")
    print(f"       {file_path.parent}")
    print("\nFiles found in that folder:")
    for item in file_path.parent.iterdir():
        print("  -", item.name)
    raise SystemExit

# 1. Load the Excel file
df = pd.read_excel(file_path)
print("File loaded successfully!\n")

# 2. Number of rows and columns
rows, cols = df.shape
print("=" * 50)
print("1) DATASET SIZE")
print("=" * 50)
print(f"Rows:    {rows}")
print(f"Columns: {cols}\n")

# 3. All column names
print("=" * 50)
print("2) COLUMN NAMES")
print("=" * 50)
for i, name in enumerate(df.columns, start=1):
    print(f"{i}. {name}")
print()

# 4. First five rows
print("=" * 50)
print("3) FIRST FIVE ROWS")
print("=" * 50)
pd.set_option("display.max_columns", None)  # show every column
pd.set_option("display.width", 200)         # avoid wrapping
print(df.head())
print()

# 5. Data type of each column
print("=" * 50)
print("4) DATA TYPES")
print("=" * 50)
print(df.dtypes)
print()

# 6. Missing values in each column
print("=" * 50)
print("5) MISSING VALUES PER COLUMN")
print("=" * 50)
print(df.isnull().sum())
print()

# 7. Duplicate rows
print("=" * 50)
print("6) DUPLICATE ROWS")
print("=" * 50)
duplicate_count = df.duplicated().sum()
print(f"Number of duplicate rows: {duplicate_count}")

if duplicate_count > 0:
    print("\nThe duplicate rows are:")
    print(df[df.duplicated(keep=False)])
else:
    print("No duplicate rows found.")

print(df.head(100))        # first 20 rows
print(df.tail(63))        # last 10 rows
print(df.iloc[100:140])     # rows 20 to 39
duplicate_count = df.duplicated().sum()
print(f"Number of duplicate rows: {duplicate_count}") # one column (use your real column name)
print("=" * 50)
print("10) DATA TYPES")
print("=" * 50)
print(df.dtypes)
print()
print("=" * 50)
print("11) MISSING VALUES PER COLUMN")
print("=" * 50)
print(df.isnull().sum())
print()

# 7. Duplicate rows
print("=" * 50)
print("12) DUPLICATE ROWS")
print("=" * 50)
duplicate_count = df.duplicated().sum()
print(f"Number of duplicate rows: {duplicate_count}")

if duplicate_count > 0:
    print("\nThe duplicate rows are:")
    print(df[df.duplicated(keep=False)])
else:
    print("No duplicate rows found.")
