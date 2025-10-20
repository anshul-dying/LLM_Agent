import os
import subprocess
from google.genai import types


MAX_CHARS = 10000

def get_files_info(working_directory, directory='.'):
    full_path = os.path.join(working_directory, directory)

    # absolute working path
    abs_working = os.path.abspath(working_directory)
    abs_full = os.path.abspath(full_path)

    if not abs_full.startswith(abs_working):
        print(f'Result for "{directory}" directory:')
        print(f'    Error: Cannot list "{directory}" as it is outside the permitted working directory')
        return
    if not os.path.isdir(abs_full):
        print(f'Result for "{directory}" directory:')
        print(f'    Error: "{directory}" is not a valid directory')
        return

    label = 'current directory' if directory == '.' else f'"{directory}" directory'
    print(f'Result for {label}:')
    for file in  os.listdir(abs_full):
        path = os.path.join(abs_full, file)
        print(f"- {file}: file_size={os.path.getsize(path)} is_dir={os.path.isdir(path)}")
    

def get_file_content(working_directory, file_path):
    abs_working = os.path.abspath(working_directory)
    abs_full = os.path.abspath(os.path.join(working_directory, file_path))

    if not os.path.commonpath([abs_working, abs_full]) == abs_working:
        print(f'Error: Cannot read "{file_path}" as it is outside the permitted working directory')
        return
    if not os.path.isfile(abs_full):
        print(f'Error: File not found or is not a regular file: "{file_path}"')
        return
    

    with open(abs_full, 'r') as f:
        contents = f.read(MAX_CHARS)

    print(contents)
    # print(abs_working)
    # print(abs_full)
    # print(file_path)

def write_file(working_directory, file_path, content):
    abs_working = os.path.abspath(working_directory)
    abs_full = os.path.abspath(os.path.join(working_directory, file_path))

    if not os.path.commonpath([abs_working, abs_full]) == abs_working:
        print(f'Error: Cannot write to "{file_path}" as it is outside the permitted working directory')
        return
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(abs_full), exist_ok=True)

    with open(abs_full, 'w') as f:
        f.write(content)

    print(f'Successfully wrote to "{file_path}" ({len(content)} characters written)')


def run_python_file(working_directory, file_path, args=[]):
    abs_working = os.path.abspath(working_directory)
    abs_full = os.path.abspath(os.path.join(working_directory, file_path))

    if not os.path.commonpath([abs_working, abs_full]) == abs_working:
        print(f'Error: Cannot execute "{file_path}" as it is outside the permitted working directory')
        return
    if not os.path.isfile(abs_full):
        print(f'Error: File "{file_path}" not found.')
        return
    
    if not abs_full.endswith('.py'):
        print(f'Error: "{file_path}" is not a Python file.')

    cmd = ['uv', 'run', abs_full] + args
    try:
        completed_process = subprocess.run(
            cmd,
            cwd=abs_working,
            capture_output=True,
            text=True,
            timeout=30
        )

        output_parts = []

        if completed_process.stdout:
            output_parts.append(f"STDOUT: {completed_process.stdout}")
        if completed_process.stderr:
            output_parts.append(f"STDERR: {completed_process.stderr}")
        if completed_process.returncode != 0:
            output_parts.append(f"Process exited with code {completed_process.returncode}")

        if not output_parts:
            print("No output produced.")
        print("\n".join(output_parts))

    except Exception as e:
        print( f"Error: executing Python file: {e}")



# Function Declaration to feed into LLM
schema_get_files_info = types.FunctionDeclaration(
    name='get_files_info',
    description='Lists files in the specified directory along with their sizes, constrained to the working directory.',
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            'directory': types.Schema(
                type=types.Type.STRING,
                description='The directory to list files from, relative to the working directory. If not provided, lists files in the working directory itself.'
            )
        }
    )
)

schema_get_file_content = types.FunctionDeclaration(
    name='get_file_content',
    description='Reads the contents of a text file within the permitted working directory, up to MAX_CHARS characters.',
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            'file_path': types.Schema(
                type=types.Type.STRING,
                description='Path to the file (relative to the working directory) whose content should be read.'
            )
        },
        required=['file_path']
    )
)

schema_write_file = types.FunctionDeclaration(
    name='write_file',
    description='Writes text content to a specified file within the permitted working directory. Creates parent directories if needed.',
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            'file_path': types.Schema(
                type=types.Type.STRING,
                description='Relative path of the file to write to within the working directory.'
            ),
            'content': types.Schema(
                type=types.Type.STRING,
                description='The text content to write into the file.'
            )
        },
        required=['file_path', 'content']
    )
)

schema_run_python_file = types.FunctionDeclaration(
    name='run_python_file',
    description='Executes a Python file within the permitted working directory using "uv run", capturing its stdout, stderr, and exit code.',
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            'file_path': types.Schema(
                type=types.Type.STRING,
                description='Relative path of the Python file to execute.'
            ),
            'args': types.Schema(
                type=types.Type.ARRAY,
                items=types.Schema(type=types.Type.STRING),
                description='Optional list of command-line arguments to pass to the Python script.'
            )
        },
        required=['file_path']
    )
)


available_functions = types.Tool(
    function_declarations=[
        schema_get_files_info, 
        schema_get_file_content,
        schema_write_file,
        schema_run_python_file
    ]
)