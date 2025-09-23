from openai import OpenAI

endpoint = "https://pf-t214-openai-ussc.openai.azure.com/openai/v1/"
deployment_name = "gpt-4_1-mini-gs-2025-04-14"
api_key = "0d845596993b45c69f5f50b97fb50b6c"

client = OpenAI(
    base_url=endpoint,
    api_key=api_key
)

completion = client.chat.completions.create(
    model=deployment_name,
    messages=[
        {
            "role": "user",
            "content": "What is the capital of France?",
        }
    ],
)

print(completion.choices[0].message)