import json

from autoforge.llm.client import gemini


class AgentBrain:

    def choose_action(
        self,
        goal,
        memory,
        tools,
    ):

        tool_descriptions = []

        for tool in tools:
            tool_descriptions.append(
                {
                    "name": tool.qualified_name,
                    "description": tool.description,
                }
            )

        prompt = f"""
                    You are an autonomous software engineering agent.

                    Goal:
                    {goal}

                    Current Memory:
                    {memory}

                    Available Tools:
                    {json.dumps(tool_descriptions, indent=2)}

                    Return ONLY valid JSON.

                    Tool Call Example:

                    {{
                    "type":"tool",
                    "tool":"filesystem.read_file",
                    "args": {{
                        "path":"README.md"
                    }}
                    }}

                    Subagent Example:

                    {{
                    "type":"subagent",
                    "agent":"research"
                    }}

                    Finish Example:

                    {{
                    "type":"finish"
                    }}
                """

        response = gemini.generate(prompt)

        return json.loads(response)