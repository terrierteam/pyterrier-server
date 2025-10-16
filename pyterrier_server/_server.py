# server.py
import asyncio
from flask import Flask, request, jsonify, render_template
from pyterrier_server._loader import load_pipeline
from fastmcp import Client
from openai import OpenAI

import os, logging, pandas as pd

logger = logging.getLogger("pyterrier_server")
logging.basicConfig(level=logging.INFO)

async def getMCP(mcp_url):
    flag = False
    async with Client(mcp_url) as client:
        if await client.list_tools()!=[]:
            flag = True
    return flag

def create_app():
    app = Flask(__name__)
    pipelines = load_pipeline()
    app.config['PIPELINES'] = pipelines
    app.config['MCP_TOOLS'] = {}
    app.config["OPENAI_CLIENT"] = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
        )
    app.json.sort_keys = False

    # --- Detect MCP ---
    mcp_url = os.environ.get("PYTERRIER_MCP_URL")
    if mcp_url:
        mcp_url = os.environ.get("PYTERRIER_MCP_URL")
        print(f"Connecting to MCP server at {mcp_url}")
        app.config["MCP_EXISTS"] = asyncio.run(getMCP(mcp_url))

    # --- Auto-create endpoints for each pipeline ---
    def make_endpoint(pipe, name):
        def endpoint_func():
            body = request.get_json(force=True, silent=True) or {}
            try:
                # Determine input based on pipeline name
                if name == "doc2query":
                    df_input = pd.DataFrame([{
                        "docno": str(body.get("docno") or 1),
                        "text": body.get("text") or body.get("q") or ""
                    }])
                else:
                    df_input = pd.DataFrame([{
                        "qid": str(body.get("qid") or 1),
                        "query": body.get("query") or body.get("q") or ""
                    }])

                result = pipe(df_input)

                if isinstance(result, pd.DataFrame):
                    return jsonify(result.to_dict("records"))
                return jsonify(result)
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        return endpoint_func

    # Register endpoints
    if isinstance(pipelines, dict):
        for name, info in pipelines.items():
            pipe = info.get("pipeline")
            if not pipe:
                continue
            endpoint = f"/pipeline/{name}"
            app.add_url_rule(endpoint, endpoint, make_endpoint(pipe, name), methods=["POST"])
            logger.info(f"Registered pipeline endpoint: {endpoint}")


    # --- AI endpoint using MCP tools ---
    @app.route('/ai', methods=['POST'])
    def ai():
        body = request.get_json(force=True, silent=True) or {}
        user_input = body.get("input") or body.get("query") or body.get("text") or body.get("q") or ""
        mcp_tools = app.config.get("MCP_EXISTS", {})
        if not mcp_tools:
            return jsonify({"error": "No MCP tools available"}), 400

        try:
            client = app.config["OPENAI_CLIENT"]

            resp = client.responses.create(
                model=os.getenv("OPENAI_MODEL"),
                tools=[{
                        "type": "mcp",
                        "server_label": "PYTERRIER_MCP",
                        "server_description": "An MCP server that contains multiple information retrieval pipelines",
                        "server_url": f"{mcp_url}",
                        "require_approval": "never",
                    }],
                input=[
                    {"role": "system", "content": (
                        """
                        You are an AI system with access to multiple MCP tools. Each tool is defined by its name and function. 
                        Your task is to:

                        1. Understand the user's request.
                        2. Automatically select and invoke the most appropriate tool to fulfill the request.

                        Critical rules:
                        - Always use a tool if one is appropriate; do not attempt to generate the answer yourself.
                        - Return exactly what the tool outputs, without altering, summarizing, or explaining it.
                        - Do not mention or describe the tool you used—just return its raw output.
                        - Only if no tool is suitable, return a brief, factual message explaining why no tool can be used.
                        - Never add extra commentary, formatting, or text beyond the tool's output.
                        """
                    )},
                    {"role": "user", "content": user_input},
                ],
            )

            logger.info("resp\n:"+str(resp))

            # Log tools used (if the response has tool info)
            tools_used = getattr(resp, "tool_usage", None)
            if tools_used is None or tools_used == []:
                tools_used = []

                if hasattr(resp, "output") and resp.output:
                    for item in resp.output:
                        if item.__class__.__name__ == "McpCall":
                            tools_used.append({
                                "name": item.name,
                                "output": item.output
                            })

            logger.info(f"Tools used: {tools_used}")


            return jsonify({"output": resp.output_text, "tools_used": tools_used or []})

        except Exception as e:
            return jsonify({"error": str(e)}), 500




    @app.route('/', methods=['GET'])
    def index():
        return render_template('index.html')

    @app.route('/config', methods=['GET'])
    def config():
        pipelines = app.config['PIPELINES']
        available = []

        if isinstance(pipelines, dict):
            for name, info in pipelines.items():
                available.append({
                    "name": name,              
                    "task": info.get('task') or name 
                })

        return jsonify({
            "available_pipelines": available,
            "mcp_enabled": bool(app.config.get('MCP_EXISTS'))
        })

    for rule in app.url_map.iter_rules():
        methods = ",".join(rule.methods)
        print(f"{rule.endpoint}: {rule} [{methods}]")

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PYTERRIER_SERVER_PORT", 8000))
    host = os.environ.get("PYTERRIER_SERVER_HOST", "0.0.0.0")
    app.run(host=host, port=port, debug=True)
