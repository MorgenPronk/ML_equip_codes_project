print("importing libraries...")
from pydantic import BaseModel, ValidationError, Field
from openai import AzureOpenAI
import pandas as pd
import json
from dotenv import load_dotenv
import os
from log_error import log_error
from tqdm import tqdm

print("loading environment variables...")
load_dotenv() # Load environment variables from .env file


# Will hardcode the API and Endpoint for now
# Get the model and endpoint from environment variables
# The model, api_version, api key, and endpoint_url should be set in the .env file because they are all unique to the model used.
API_key = os.getenv("API_key")
endpoint_url = os.getenv("endpoint_url")
deployment = os.getenv("deployment")
api_version = os.getenv("api_version")

print("creating openai client...")
client = AzureOpenAI(
    api_version=api_version,
    azure_endpoint= endpoint_url,
    api_key=API_key,
)

# class Hierarchy_output(BaseModel):
#     level_4: str
#     level_4_1: str
#     level_5: str
#     level_5_1: str
#     level_6: str
#     level_6_1: str
#     level_7: str
#     level_8: str
#     subclass: str

class Hierarchy_output(BaseModel):
    level_4: str = Field(alias="level 4")
    level_4_1: str = Field(alias="level 4.1")
    level_5: str = Field(alias="level 5")
    level_5_1: str = Field(alias="level 5.1")
    level_6: str = Field(alias="level 6")
    level_6_1: str = Field(alias="level 6.1")
    level_7: str = Field(alias="level 7")
    level_8: str = Field(alias="level 8")
    subclass: str

    class Config:
        populate_by_name = True  # Allows using either alias or field name

print("reading instructions...")
# Get the system prompt from a text file
system_prompt_path = os.path.join("prompts", "system_prompt.txt")
with open(system_prompt_path, "r") as file:
    system_prompt = file.read()

with open("hierarchy_examples.txt", "r") as file:
    hierarchy_examples = file.read()

def convert(obj):
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    if pd.isna(obj):  # Handles NaT, NaN, None, etc.
        return None
    raise TypeError(f"Type {type(obj)} not serializable")

# def normalize_keys(data):
#     """
#     Normalize the keys of the input dictionary to match the expected format.
#     """
#     mapping = {
#         "level 4": "level_4",
#         "level 4.1": "level_4_1",
#         "level 5": "level_5",
#         "level 5.1": "level_5_1",
#         "level 6": "level_6",
#         "level 6.1": "level_6_1",
#         "level 7": "level_7",
#         "level 8": "level_8",
#     }
#     return {mapping.get(k, k): v for k, v in data.items()}

def generate_hierarchy_with_rety(record_str, system_prompt=system_prompt, hierarchy_examples=hierarchy_examples):
    # First attempt to generate hierarchy
    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": f"{system_prompt} \n\n{hierarchy_examples}"},
            {"role": "user", "content": record_str},
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
    )
    output_json = response.choices[0].message.content
    #input(f"Try 1: Output JSON:\n{output_json}\n")
    
    # Verify the output JSON structure
    try:
        hierarchy = Hierarchy_output.model_validate_json(output_json)
        return hierarchy
    # except ValidationError as e:
    #     input(f"try 1 - Output_json:\n{output_json}\n")
    #     #try normalizing the keys
    #     normalized_data = normalize_keys(json.loads(output_json))
    #     input(f"try 2 - Normalized Data:\n{normalized_data}\n")
    #     try:
    #         # retest the normalized data
    #         hierarchy = Hierarchy_output.model_validate(normalized_data)
    #         return hierarchy
    except ValidationError as e_2:
        # Ask the LLM to fix the output
        fix_prompt = (
            f"The following output did not match the expected schema due to this error:\n{e_2}\n"
            f"Original output:\n{output_json}\n"
            "Please fix the output to match the expected schema"
        )
        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": f"{system_prompt} \n\n{hierarchy_examples}"},
                {"role": "user", "content": fix_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
        )
        output_json = response.choices[0].message.content
        #input(f"final try - output_json:\n{output_json}\n")
        try:
            hierarchy = Hierarchy_output.model_validate_json(output_json)
            return hierarchy
        except ValidationError as e_3:
            error_message = f"Error validating hierarchy output: {e_3}\n"
            print(error_message)
            log_error(error_message)

def loop_equipment(xl_path, jsonl_path, start_index=0):
    """
    Loop through all of the equipment records in the Excel file and generate a hierarchy for each record.
    """
 
    df = pd.read_excel(xl_path)

    # Check that the JSON dump file exists, if not create it
    processed_indices = set()
    if os.path.exists(jsonl_path):
        with open(jsonl_path, 'r') as f:
            for line in f:
                try:
                    record = json.loads(line)
                    processed_indices.add(record.get("record_index"))
                except json.JSONDecodeError:
                    error_message = f"Error decoding JSON line: {line}\n"
                    print(error_message)
                    log_error(error_message)
                    continue
    
    # Open the JSONL file in append mode - if it doesn't exist, it will be created automatically by open()
    with open(jsonl_path, "a") as f:
        # Loop through the DataFrame starting from start_index
        for index, row in tqdm(df.iterrows(), total=len(df), desc="Processing records"):
            if index < start_index or index in processed_indices:
                continue

            # Get row information
            record_dict = row.to_dict()
            record_str = json.dumps(record_dict, default=convert)

            log_error(f"---INDEX {index} - Generating hierarchy for record with AI---")
            hierarchy = generate_hierarchy_with_rety(record_str, system_prompt, hierarchy_examples)
            # try:
            #     # Get row information
            #     record_dict = row.to_dict()
            #     record_str = json.dumps(record_dict, default=convert)

            #     # Generate hierarchy for each record
            #     print(f"Generating hierarchy for record {index + 1} with AI...")
            #     response = client.chat.completions.create(
            #         model=deployment,
            #         messages=[
            #             {"role": "system", "content": f"{system_prompt} \n\n{hierarchy_examples}"},
            #             {"role": "user", "content": record_str},
            #             ],
            #             response_format={"type": "json_object"},
            #             temperature=0.0,
            #     )

            #     output_json = response.choices[0].message.content

            #     # Verify the output JSON structure
            #     hierarchy = Hierarchy_output.model_validate_json(output_json)

            # print to the JSON Output file
            try:
                hierarchy_dict = hierarchy.model_dump()
                f.write(json.dumps(hierarchy_dict) + "\n")
                f.flush()  # Ensure data is written to the file immediately
                # print(f"dumped hierarchy to JSONL file {jsonl_path}...\n{hierarchy_dict}\n")

            except Exception as e:
                error_message = f"Error processing record {index + 1}: {e}\n"
                print(error_message)

                # Append the error to a log file
                log_error(error_message)
                continue

def jsonl_to_excel(jsonl_path, excel_path):
    """
    Convert the JSONL file to an Excel file.
    """
    data = []
    with open(jsonl_path, 'r') as f:
        for line in f:
            try:
                record = json.loads(line)
                data.append(record)
            except json.JSONDecodeError:
                error_message = f"Error decoding JSON line: {line}\n"
                print(error_message)
                log_error(error_message)
                continue

    df = pd.DataFrame(data)
    df.to_excel(excel_path, index=False)

def main():
    """
    Main function to run the script.
    """
    # Define the paths for the input Excel file and output JSONL file
    xl_path = os.path.join("data", "Current JDE Equipment Table 6-2-25.xlsx") # equipment_data.xlsx"
    jsonl_path = os.path.join("outputs", "hierarchy_output.jsonl") # "hierarchy_output.jsonl"
    excel_output_path = os.path.join("outputs", "hierarchy_output.xlsx") # "hierarchy_output.xlsx"
    error_log_path = os.path.join("logs", "error_log.txt") # "error_log.txt"

    # Loop through the equipment records and generate hierarchy
    loop_equipment(xl_path, jsonl_path)

    # Convert the JSONL file to an Excel file
    jsonl_to_excel(jsonl_path, excel_output_path)

if __name__ == "__main__":
    main()
    print("Script completed successfully.")