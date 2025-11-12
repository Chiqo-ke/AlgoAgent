import ast

def insert_snippet_if_missing(file_path: str, indicator_name: str, snippet: str) -> bool:
    """Appends a Python snippet to a file if a function for the indicator_name does not already exist.

    This function parses the Python file to check for a top-level function
    with the given indicator_name (case-insensitive).

    Args:
        file_path (str): The absolute path to the Python file to modify.
        indicator_name (str): The name of the indicator function to check for.
        snippet (str): The Python code snippet to append to the file.

    Returns:
        bool: True if the file was changed, False otherwise.
    """
    try:
        with open(file_path, 'r') as f:
            file_content = f.read()
    except FileNotFoundError:
        # If the file doesn't exist, we can create it with the snippet.
        file_content = ""

    tree = ast.parse(file_content)

    # Check if a function with the indicator name already exists
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.lower() == indicator_name.lower():
            # Function already exists, do nothing.
            return False

    # If the function does not exist, append the snippet to the file.
    new_content = file_content.strip() + "\n\n" + snippet.strip() + "\n"

    with open(file_path, 'w') as f:
        f.write(new_content)
    
    return True
