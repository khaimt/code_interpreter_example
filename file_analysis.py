from openai import OpenAI
import random
import json
import os
import shutil

# all openai compatible can be used here
# please export OPENAI_API_KEY=your_key; if you are using Functionary models, you can set OPENAI_API_KEY to any values
# If you are using OpenAI models, the default base_url is "https://api.openai.com/v1";
# if you are using Functionary models, you need to set base_url to the IP, Port of Functionary server, E.g. base_url="http://localhost:8000/v1"

client = OpenAI(base_url="https://api.openai.com/v1")
tools = []
tools.append(
    {
        "type": "function",
        "function": {
            "name": "execute_code",
            "description": "Execute Python code in a Jupyter Notebook environment with basic dependencies installed. Please use this tool when some task can be done by executing code such as: perform arithmetic operations, perform data analysis, perform data visualization, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "The Python code to execute. It should be formatted as a valid Python script.",
                    }
                },
                "required": ["code"],
            },
        },
    }
)

# Simulate the jupyter notebook execution
from python_sandbox import create_notebook, execute_code

notebook = create_notebook("test")


def execute_code_tool(code):
    return execute_code(code, notebook)


def upload_file():
    current_folder = os.path.dirname(os.path.abspath(__file__))
    dst_file = os.path.join(current_folder, "data_folder/China_gdp_growth.csv")
    return dst_file, "file-kjmlnsy2ROyJwL4ZdvJBhXav"  # a random file_id


# simulate when user upload a file
file_path, file_id = upload_file()

messages = [
    {  # When user uploads a file, we will use the upload API to upload the file to a folder in python sandbox
        "role": "system",
        "content": f"User uploaded file with ID '{file_id}' to: {file_path}\n",
    },
    {
        "role": "user",
        "content": "what is the average GDP growth rate of China since 2020",
    },
]

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=messages,
    tools=tools,
)

model_name = "gpt-4o-mini"  # you can use any openai compatible model, e.g. functionary-small-v3.1
# Execute this message by a loop


while True:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=tools,
        tool_choice="auto",
        temperature=0.0,  # should be 0.0 in cases tools are not empty
    )
    response_message = response.choices[0].message
    messages.append(response_message.dict(exclude_none=True))
    if response_message.tool_calls:  # if the model decided to use tools
        content = response_message.content
        if content:
            print(f"ASSISTANT: {content}")
        # Process each tool call
        for tool_call in response_message.tool_calls:
            # Get the function name and arguments
            function_name = tool_call.function.name
            print(f"ASSISTANT USE TOOL: {function_name}")
            # Execute the appropriate tool
            if (
                "functionary" in model_name.lower()
            ):  # this is how function implemented code interpreter
                assert (
                    function_name == "python"
                )  # in functionary, when {"type": "code_interpreter"} is added to the tools, the function name is always "python"
                code = tool_call.function.arguments
            else:  # function_name=execute_code, when model=gpt-4o-mini
                assert function_name == "execute_code"
                code = json.loads(tool_call.function.arguments)["code"]

            result = execute_code_tool(code)
            print(f"CODE: \n```python\n{code}\n```")
            print("RESULT: ", result)
            # Append the tool result to messages
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )

        # Add the assistant's response to messages

    else:
        # If no tool calls, the execution is done, the content is the final result
        print("FINAL_RESULT: ", response_message.content)
        break
