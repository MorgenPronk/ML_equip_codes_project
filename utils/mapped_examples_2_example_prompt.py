import pandas as pd

# Load mapped examples file (output structure)
mapped_df = pd.read_excel("./data/examples_mapped.xlsx", engine="openpyxl")
mapped_df = mapped_df.dropna(how="all")
mapped_df.columns = mapped_df.columns.str.strip().str.lower()  # Clean column names
# print(mapped_df.head()) # debugging

# Load raw input data file
equipment_df = pd.read_excel("./data/Current JDE Equipment Table 6-2-25.xlsx", engine="openpyxl")
equipment_df.columns = equipment_df.columns.str.strip()  # Clean column names

# Output structure column names
output_columns = [
    "level 4", "level 4.1", "level 5", "level 5.1",
    "level 6", "level 6.1", "level 7", "level 8", "subclass"
]

# Open prompt file for writing
with open("./prompts/hierarchy_examples.txt", "w", encoding="utf-8") as f:
    f.write("Below are examples of inputs and outputs\n\n")

    example_count = 1
    for _, row in mapped_df.iterrows():
        tag = str(row.get("level 6.1", "")).strip()

        # Match in input source file
        match = equipment_df[
            (equipment_df["Tag Number"].astype(str).str.strip() == tag) |
            (equipment_df["Serial Number"].astype(str).str.strip() == tag)
        ]

        if not match.empty:
            input_row = match.iloc[0]
            input_fields = {col: ("" if pd.isna(val) else val) for col, val in input_row.items()}

            # Format Input
            f.write(f"Example {example_count} Input:\n")
            f.write(str(input_fields).replace("'", '"') + "\n\n")

            # Format Output
            output_fields = {col: ("" if pd.isna(row[col]) else row[col]) for col in output_columns}
            f.write(f"Example {example_count} Output:\n")
            f.write(" {\n")
            for key, val in output_fields.items():
                f.write(f'    "{key}"  : "{val}",\n')
            f.seek(f.tell() - 2, 0)  # Remove last comma
            f.write("\n }\n\n")

            example_count += 1