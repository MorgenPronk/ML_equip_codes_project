from pydantic import BaseModel
from openai import AzureOpenAI
import pandas as pd
import json
from dotenv import load_dotenv
import os

load_dotenv() # Load environment variables from .env file


# Will hardcode the API and Endpoint for now
# Get the model and endpoint from environment variables
# The model, api_version, api key, and endpoint_url should be set in the .env file because they are all unique to the model used.
API_key = os.getenv("API_key")
endpoint_url = os.getenv("endpoint_url")
deployment = os.getenv("deployment")
api_version = os.getenv("api_version")

client = AzureOpenAI(
    api_version=api_version,
    azure_endpoint= endpoint_url,
    api_key=API_key,
)

class Hierarchy_output(BaseModel):
    level_4_0: str
    level_4_1: str
    level_5_0: str
    level_5_1: str
    level_6_0: str
    level_7_0: str
    level_8_0: str
    subclass: str

# Get the system prompt from a text file
with open("system_prompt.txt", "r") as file:
    system_prompt = file.read()

with open("hierarchy_examples.txt", "r") as file:
    hierarchy_examples = file.read()

def convert(obj):
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    if pd.isna(obj):  # Handles NaT, NaN, None, etc.
        return None
    raise TypeError(f"Type {type(obj)} not serializable")

# Get the equipment info from a xlsx file
xl_path = "./Current JDE Equipment Table 6-2-25.xlsx"
df = pd.read_excel(xl_path)

record = df.iloc[1454]  # taking just an example for testing
record_dict = record.to_dict()
record_str = json.dumps(record_dict, default=convert)

response = client.chat.completions.create(
    model = deployment,
    messages=[
        {"role": "system", "content": f"{system_prompt} \n\n{hierarchy_examples}"},
        {"role": "user", "content": record_str}
    ],
    response_format={"type": "json_object"},
)

output_json = response.choices[0].message.content
hierarchy = Hierarchy_output.model_validate_json(output_json)
print(hierarchy)