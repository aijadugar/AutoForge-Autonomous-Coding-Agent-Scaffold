import json

from autoforge.llm.client import gemini


def generate_plan(
    goal: str,
    context: str = "",
):

    prompt = f"""
                Goal:
                {goal}

                Context:
                {context}

                Create execution plan.

                Return ONLY JSON array.

                Example:

                [
                {{
                    "title":"Inspect repository",
                    "description":"Analyze repository structure"
                }},
                {{
                    "title":"Identify relevant files",
                    "description":"Find files related to goal"
                }}
                ]
                """

    response = gemini.generate(prompt)

    print("==== GEMINI PLAN RESPONSE ====")
    print(response)
    print("==============================")

    return json.loads(response)