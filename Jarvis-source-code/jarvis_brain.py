from brain import get_notes
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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"
)

brain = get_notes()

while True:

    q = input("\nYou: ")

    prompt = f"""
Brain Knowledge:

{brain[:5000]}

Question:

{q}
"""

    response = client.chat.completions.create(
        model="openrouter/auto",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    print(
        "\nJarvis:",
        response.choices[0].message.content
    )