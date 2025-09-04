import pandas as pd
import openpyxl
import json

def normalize_dict(d):
    return {str(k).strip().lower(): v for k, v in d.items()}

examples_path = "./data/Consolidated_examples.xlsx"
code_map_path = "./data/code_map.json"

df = pd.read_excel(examples_path, engine='openpyxl')
df = df.dropna(how='all')  # Drop rows where all elements are NaN

with open(code_map_path, 'r') as file:
        code_map = json.load(file)

# map of the examples dataframe's column names to which dictionary to use for the code_map
columns_to_code_map_dict = {
      "Level 4": code_map["L4_codes"],
      "Level 4.1": code_map["L4_1_codes"],
      "Level 5": code_map["L5_codes"],
      "Level 5.1": code_map["L5_1_codes"],
}

for col, code_dict in columns_to_code_map_dict.items():
      if col in df.columns:
            try:
                  normal_dict = normalize_dict(code_dict)
                  df[col] = df[col].map(lambda x: normal_dict.get(str(x).strip().lower(), x))
            except Exception as e:
                  print(f"Error processing column {col}: {e}")
                  
# Save the modified DataFrame to a new Excel file            
df.to_excel("./data/examples_mapped.xlsx", index=False)

