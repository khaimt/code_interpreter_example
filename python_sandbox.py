import nbformat
from nbformat.v4 import new_notebook, new_code_cell
import json
from nbclient import NotebookClient

def create_notebook(name: str) -> nbformat.NotebookNode:
    """Creates a new Jupyter notebook with the given name.
    
    Args:
        name (str): Name of the notebook to create
        
    Returns:
        nbformat.NotebookNode: The created notebook object
    """
    nb = new_notebook()
    nb.metadata = {
        'kernelspec': {
            'display_name': 'Python 3',
            'language': 'python',
            'name': 'python3'
        }
    }
    return nb

def execute_code(code: str, nb: nbformat.NotebookNode) -> dict:
    """Executes Python code in a Jupyter notebook environment and returns the output.
    
    Args:
        code (str): Python code to execute
        
    Returns:
        dict: Dictionary containing execution results with keys:
            - output: String containing stdout/stderr output
            - display_data: List of display data (e.g. plots, images)
            - error: Error message if execution failed
    """    
    # Add code cell
    cell = new_code_cell(code)
    nb.cells.append(cell)
    
    # Execute notebook
    client = NotebookClient(nb, timeout=600)
    try:
        client.execute()
        
        # Extract outputs
        result = {
            "output": "",
            "display_data": [],
            "error": None
        }
        
        for output in cell.outputs:
            if output.output_type == "stream":
                result["output"] += output.text
            elif output.output_type == "display_data":
                result["display_data"].append(output.data)
            elif output.output_type == "error":
                result["error"] = f"{output.ename}: {output.evalue}"
            elif output.output_type == "execute_result":
                result["output"] = str(output.data.get('text/plain', ''))
                
        return result
        
    except Exception as e:
        return {
            "output": "",
            "display_data": [],
            "error": str(e)
        }


def test():
    nb = create_notebook("test")
    code = "a=[1,2,3,4]\nmax(a) + 5"
    result = execute_code(code, nb)
    print(result)

if __name__ == "__main__":
    test()
