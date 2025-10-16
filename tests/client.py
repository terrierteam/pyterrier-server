import asyncio
from fastmcp import Client
import os
from dotenv import load_dotenv
load_dotenv()
import time

async def main():
    mcp_url = os.environ.get("PYTERRIER_MCP_URL")
    print(f"Connecting to MCP server at {mcp_url}")
    result=None
    async with Client(mcp_url) as client:
        print("=====================")
        print("Available tools:", await client.list_tools())
        print("Calling MSMARCO-search tool... Do not cancel. This may take a while if the server is cold.")
        print("=====================")
        result = await client.call_tool(
            name="MSMARCO-search", 
            arguments={"qid": "1", "query": "give me documents that talk about goldfish"}
        )
        print("Search Result:\n", result)
        print("=====================")
        time.sleep(5)
        result = await client.call_tool(
            name="ragwiki-rag", 
            arguments={"qid": "1", "query": "give me documents that talk about goldfish"}
        )
        print("RAG Result:\n", result)
        print("=====================")
        time.sleep(5)
        result = await client.call_tool(
            name="doc2query", 
            arguments={"docno": "1", "text": "give me documents that talk about goldfish"}
        )
        print("doc2query Result:\n", result)
        print("=====================")
asyncio.run(main())