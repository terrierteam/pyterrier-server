# _mcp_server.py
import os
import logging
from fastmcp import FastMCP
import pandas as pd
from pydantic import BaseModel, create_model, ValidationError
import re

logger = logging.getLogger(__name__)
logging.getLogger("uvicorn.access").setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO)

TYPE_MAP = {
    "string": str,
    "int": int,
    "float": float,
    "bool": bool,
    "list": list,
    "dict": dict,
}

def schema_to_pydantic(name: str, schema) -> BaseModel:
    """
    Converts schema (dict or list) to a Pydantic model.
    Supports:
      - dict: {"field": type, ...}
      - list of dicts: [{"phrase": "name", "type": str, ...}, ...]
    Automatically sanitizes field names.
    """
    schema = [ i for i in schema if i is not None]

    def sanitize_field_name(s):
        """Convert arbitrary string to a valid Python identifier."""
        if not s:
            return "field"
        s = re.sub(r'\W|^(?=\d)', '_', s)
        return s.strip('_') or "field"

    fields = {}

    if isinstance(schema, dict):
        # Normal case
        for k, v in schema.items():
            fields[sanitize_field_name(k)] = (v, ...)
    elif isinstance(schema, list):
        # List of field definitions
        for i, entry in enumerate(schema):
            if not isinstance(entry, dict):
                raise TypeError(f"List schema entries must be dicts, got {type(entry)}")
            # Determine field name
            field_name = entry.get("phrase") or entry.get("name") or entry.get("field") or f"field_{i}"
            field_type = entry.get("type", str)
            if isinstance(field_type, str):
                field_type = TYPE_MAP.get(field_type.lower(), str)
            fields[sanitize_field_name(field_name)] = (field_type, ...)
    else:
        raise TypeError(f"Schema for {name} must be dict or list, got {type(schema)}")
    
    return create_model(name, **fields)



# ---------------------------
# Utility to wrap pipeline function with input/output validation
# ---------------------------
def wrap_pipeline(pipeline_func, input_schema, output_schema):
    InputModel = schema_to_pydantic("InputModel", input_schema)

    # --- extract argument names from schema ---
    def get_arg_names(schema):
        if isinstance(schema, dict):
            return list(schema.keys())
        elif isinstance(schema, list):
            names = []
            for i, entry in enumerate(schema):
                if not isinstance(entry, dict):
                    names.append(f"field_{i}")
                    continue
                name = (
                    entry.get("phrase")
                    or entry.get("name")
                    or entry.get("field")
                    or f"field_{i}"
                )
                # sanitize to match what schema_to_pydantic does
                name = re.sub(r"\W|^(?=\d)", "_", name)
                name = name.strip("_") or f"field_{i}"
                names.append(name)
            return names
        else:
            raise TypeError(f"Invalid input schema type: {type(schema)}")

    arg_names = get_arg_names(input_schema)
    arg_str = ", ".join(arg_names)

    # --- dynamically build the function source ---
    code = f"""
def tool_func({arg_str}) -> list[dict]:
    # Cast inputs to the expected types
    input_kwargs = {{}}
    for field, value in locals().items():
        if field in arg_names:
            field_type = InputModel.model_fields[field].annotation
            try:
                # Only cast if type does not match
                if not isinstance(value, field_type):
                    value = field_type(value)
            except Exception as e:
                raise ValueError(f"Cannot cast '{{field}}'={{value}} to {{field_type}}: {{e}}")
            input_kwargs[field] = value

    input_obj = InputModel(**input_kwargs)
    df = pd.DataFrame([input_obj.dict()])
    result = pipeline_func(df)
    
    if isinstance(result, pd.DataFrame):
        records = result.to_dict('records')
    elif isinstance(result, dict):
        records = [result]
    elif isinstance(result, list):
        records = result

    return records
"""
    ns = {
        "InputModel": InputModel,
        "pipeline_func": pipeline_func,
        "pd": pd,
        "ValidationError": ValidationError,
        "re": re,
        "arg_names": arg_names
    }
    exec(code, ns)
    print("Created tool_func:", ns["tool_func"])
    return ns["tool_func"]



# ---------------------------
# Create FastMCP server
# ---------------------------
def mcp_port():
    port_str = os.environ.get("PYTERRIER_MCP_PORT", "8000")
    try:
        port = int(port_str)
    except ValueError:
        port = 8000
    return port

def create_mcp_server(pipelines=None):

    # mcp = FastMCP("PYTERRIER_MCP",auth=auth)
    mcp = FastMCP("PYTERRIER_MCP",stateless_http=True)
    tools = {}

    if pipelines:
        if isinstance(pipelines, dict):
            for name, info in pipelines.items():
                pipeline_func = info.get("pipeline")
                if not callable(pipeline_func):
                    continue

                input_schema = info.get("properties") or [{"phrase": "query", "type": str}]
                output_schema = info.get("outputs") or "list[dict]"
                print("info",info)
                print("output_schema",output_schema)
                description = info.get("description", f"Pipeline {name}")

                tool_func = wrap_pipeline(pipeline_func, input_schema, output_schema)
                tools[name] = mcp.tool(name=name, description=description)(tool_func)

    port = mcp_port()
    host = os.environ.get("PYTERRIER_MCP_HOST", "0.0.0.0")
    logger.info(f"Starting MCP on {host}:{port} with tools: {list(tools.keys())}")
    mcp.run(transport="http", port=port, host=host)

def main():
    from pyterrier_server._loader import load_pipeline
    pipelines = load_pipeline()
    create_mcp_server(pipelines)


# ---------------------------
# Standalone run
# ---------------------------
if __name__ == "__main__":
    main()
