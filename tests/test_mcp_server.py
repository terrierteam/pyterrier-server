# test_fastmcp_tools.py
import os
import unittest
import asyncio
import multiprocessing
import time
from fastmcp import Client

from pyterrier_server._mcp_server import create_mcp_server

# -----------------------------
# Helper to start MCP server in background
# -----------------------------
def start_server():
    os.environ["PYTERRIER_MCP_PORT"] = "8000"
    from pyterrier_server._loader import load_pipeline
    pipeline_str = os.environ.get("PYTERRIER_SERVER_PIPELINE")
    if not pipeline_str:
        os.environ["PYTERRIER_SERVER_PIPELINE"] = "functions.yaml"
    pipelines = load_pipeline()
    create_mcp_server(pipelines)

class TestFastMCPTools(unittest.IsolatedAsyncioTestCase):

    @classmethod
    def setUpClass(cls):
        # Start the MCP server in a separate process
        cls.server_process = multiprocessing.Process(target=start_server, daemon=True)
        cls.server_process.start()
        time.sleep(200)  # wait for server to start
        cls.mcp_url = "http://localhost:8000/mcp"

    @classmethod
    def tearDownClass(cls):
        # Terminate the MCP server
        cls.server_process.terminate()
        cls.server_process.join()

    async def asyncSetUp(self):
        self.client = Client(self.mcp_url)
        await self.client.__aenter__()

    async def asyncTearDown(self):
        await self.client.__aexit__(None, None, None)

    async def test_list_tools(self):
        tools = await self.client.list_tools()
        tool_names = [t.name for t in tools]
        self.assertIn("MSMARCO-search", tool_names)
        self.assertIn("ragwiki-rag", tool_names)
        self.assertIn("doc2query", tool_names)

    async def test_msmarco_search(self):
        result = await self.client.call_tool(
            name="MSMARCO-search",
            arguments={"qid": "1", "query": "goldfish"}
        )
        self.assertIn("result", result.structured_content)
        self.assertGreater(len(result.structured_content["result"]), 0)

    async def test_ragwiki_rag(self):
        result = await self.client.call_tool(
            name="ragwiki-rag",
            arguments={"qid": "1", "query": "goldfish"}
        )
        self.assertIn("result", result.structured_content)
        self.assertGreater(len(result.structured_content["result"]), 0)
        self.assertIn("qanswer", result.structured_content["result"][0])

    async def test_doc2query(self):
        result = await self.client.call_tool(
            name="doc2query",
            arguments={"docno": "1", "text": "goldfish"}
        )
        self.assertIn("result", result.structured_content)
        self.assertGreater(len(result.structured_content["result"]), 0)
        self.assertIn("querygen", result.structured_content["result"][0])


if __name__ == "__main__":
    unittest.main()
