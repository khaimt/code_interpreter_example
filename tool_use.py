from openai import OpenAI
import random
import json

# all openai compatible can be used here
# please export OPENAI_API_KEY=your_key; if you are using Functionary models, you can set OPENAI_API_KEY to any values
# If you are using OpenAI models, the default base_url is "https://api.openai.com/v1";
# if you are using Functionary models, you need to set base_url to the IP, Port of Functionary server, E.g. base_url="http://localhost:8000/v1"

client = OpenAI(base_url="https://api.openai.com/v1")

# the inputs of Tool use models are messages and tools
# Here is the format of tools in OpenAI format, if you are using Functionary models, you can use the same format
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get the weather of a city on a specific date",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The city name, e.g. San Francisco",
                    },
                    "date": {
                        "type": "string",
                        "description": "The date of the weather, format: YYYY-MM-DD, e.g. 2025-02-09",
                    },
                },
                "required": ["city", "date"],
            },
        },
    }
]
# If you are using code_interpreter tool, you can just add:
# tools.append({"type": "code_interpreter"})
# However for OpenAI models, you need to directly add the tool using type="function"

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

# Here are the example implementation of 2 tools above


def get_current_weather(city, date):
    temperature = random.randint(10, 30)
    return {"temperature": temperature, "unit": "Celsius"}


# Simulate the jupyter notebook execution
from python_sandbox import create_notebook, execute_code

notebook = create_notebook("test")


def execute_code_tool(code):
    return execute_code(code, notebook)


# messages is a list of messages, each message is a dict with role and content
messages = [
    {
        "role": "user",
        "content": "What is average temperature of San Francisco from 2024-01-01 to 2024-01-05",
    },
]

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
            if function_name == "get_current_weather":
                function_args = json.loads(tool_call.function.arguments)
                result = get_current_weather(
                    function_args["city"], function_args["date"]
                )
                print("ARGUMENTS: ", function_args)
            elif function_name == "execute_code":
                if (
                    "functionary" in model_name.lower()
                ):  # this is how function implemented code interpreter
                    code = tool_call.function.arguments
                else:
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
