# test_fastmcp_tools.py
import os
import unittest
import asyncio
import multiprocessing
import time
import httpx
from fastmcp import Client
import torch

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

        cls.mcp_url = "http://0.0.0.0:8000/mcp"

        async def wait_for_server():
            timeout = 120
            start_time = time.time()
            while True:
                try:
                    async with Client(cls.mcp_url) as client:
                        tools = await client.list_tools()
                        if isinstance(tools, list) and tools:
                            print("✅ MCP server is ready and responding with tools!")
                            break
                        print("[TEST] No tools yet, waiting...")
                except Exception:
                    pass

                if time.time() - start_time > timeout:
                    raise RuntimeError(f"❌ MCP server failed to start within {timeout} seconds")
                await asyncio.sleep(1)

        # Run the async polling loop to wait for server readiness
        asyncio.run(wait_for_server())


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

    # too havey for the github action
    # async def test_msmarco_search(self):
    #     result = await self.client.call_tool(
    #         name="MSMARCO-search",
    #         arguments={"qid": "1", "query": "goldfish"}
    #     )
    #     self.assertIn("result", result.structured_content)
    #     self.assertGreater(len(result.structured_content["result"]), 0)

    # too havey for the github action 
    # async def test_ragwiki_rag(self):
    #     if torch.cuda.is_available():
    #         result = await self.client.call_tool(
    #             name="ragwiki-rag",
    #             arguments={"qid": "1", "query": "goldfish"}
    #         )
    #         self.assertIn("result", result.structured_content)
    #         self.assertGreater(len(result.structured_content["result"]), 0)
    #         self.assertIn("qanswer", result.structured_content["result"][0])

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
