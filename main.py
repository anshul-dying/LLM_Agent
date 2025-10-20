# required
import os
from dotenv import load_dotenv
import sys

# genai
from google import genai
from google.genai import types

from functions.get_files_info import (
    schema_get_files_info,
    schema_get_file_content,
    schema_write_file,
    schema_run_python_file,
    available_functions,

    get_files_info,
    get_file_content,
    write_file,
    run_python_file
)

load_dotenv()


function_map = {
    "get_files_info": get_files_info,
    "get_file_content": get_file_content,
    "write_file": write_file,
    "run_python_file": run_python_file,
}

def call_function(function_call_part, verbose=False):
    function_name = function_call_part.name
    function_args = dict(function_call_part.args)
    function_args["working_directory"] = "./"

    if verbose:
        print(f"Calling function: {function_call_part.name}({function_call_part.args})")
    print(f" - Calling function: {function_call_part.name}")

    # check if valid function
    if function_name not in function_map:
        return types.Content(
            role="tool",
            parts=[
                types.Part.from_function_response(
                    name=function_name,
                    response={"error": f"Unknown function: {function_name}"},
                )
            ],
        )
    
    result = function_map[function_name](**function_args)

    return types.Content(
        role="tool",
        parts=[
            types.Part.from_function_response(
                name=function_name,
                response={"result": result},
            )
        ],
    )

def main():
    api_key = os.environ['GEMINI_API_KEY']
    client = genai.Client(api_key=api_key)
    
    # get prompt directly from cli
    if len(sys.argv) < 2:
        print("Usage: uv run main.py <prompt>")
        sys.exit(1)

    user_prompt = sys.argv[1]
    # print(prompt)

    system_prompt = """
    You are a helpful AI coding agent.

    When a user asks a question or makes a request, make a function call plan. You can perform the following operations:

    - List files and directories
    - Read file contents
    - Execute Python files with optional arguments
    - Write or overwrite files

    All paths you provide should be relative to the working directory. You do not need to specify the working directory in your function calls as it is automatically injected for security reasons.
    """


    verbose = "--verbose" in sys.argv

    messages = [
        types.Content(role='user', parts=[types.Part(text=user_prompt)])
    ]

    response = client.models.generate_content(
        model="gemini-2.0-flash-001",
        contents=messages,
        config=types.GenerateContentConfig(
            tools=[available_functions],
            system_instruction=system_prompt
        )
    )

    function_calls = response.function_calls or []

    if verbose:
        print(response.text)
        print(f"User prompt: {user_prompt}") 
        print(f"Prompt tokens: {response.usage_metadata.prompt_token_count}")
        print(f"Response tokens: {response.usage_metadata.candidates_token_count}")

    if not function_calls:
        print("No function calls were returned by the model.")
        return
    
    else:
        for fc in function_calls:
            function_call_result = call_function(fc, verbose=verbose)
            if verbose:
                print(f"-> {function_call_result.parts[0].function_response.response}")

if __name__ == "__main__":
    main()