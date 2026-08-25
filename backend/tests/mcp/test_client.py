import asyncio
import json

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


PROJECT_ID = "474a5dd4-9420-4fbf-97be-0a03c4b7d0b5"
MCP_URL = "http://127.0.0.1:8000/mcp"


def parse_result(result):
    """Extract the JSON payload returned by an MCP tool."""
    return json.loads(result.content[0].text)


async def main():
    async with streamablehttp_client(MCP_URL) as (
        read_stream,
        write_stream,
        _,
    ):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # 1. Verify MCP tools are available
            tools = await session.list_tools()

            expected_tools = {
                "create_run",
                "get_run_status",
                "execute_run",
                "get_reconciliation",
                "resolve_reconciliation",
                "list_project_runs",
            }

            actual_tools = {tool.name for tool in tools.tools}

            assert expected_tools.issubset(actual_tools), (
                f"Missing MCP tools: {expected_tools - actual_tools}"
            )

            print("\nMCP tools:")
            for tool in tools.tools:
                print(f"- {tool.name}")

            # 2. Create a run
            print("\nCalling create_run...")

            create_result = await session.call_tool(
                "create_run",
                {
                    "project_id": PROJECT_ID,
                },
            )

            create_data = parse_result(create_result)

            assert create_data["success"] is True

            run_id = create_data["run_id"]

            print(f"Created run: {run_id}")

            # 3. Check run status
            print("\nCalling get_run_status...")

            status_result = await session.call_tool(
                "get_run_status",
                {
                    "project_id": PROJECT_ID,
                    "run_id": run_id,
                },
            )

            status_data = parse_result(status_result)

            assert status_data["success"] is True
            assert status_data["run_id"] == run_id

            print(f"Run status: {status_data['status']}")

            # 4. Execute the run
            print("\nCalling execute_run...")

            execute_result = await session.call_tool(
                "execute_run",
                {
                    "project_id": PROJECT_ID,
                    "run_id": run_id,
                },
            )

            execute_data = parse_result(execute_result)

            assert execute_data["success"] is True

            print(
                f"Execution decision: "
                f"{execute_data.get('decision')}"
            )

            # 5. Check reconciliation state
            print("\nCalling get_reconciliation...")

            reconciliation_result = await session.call_tool(
                "get_reconciliation",
                {
                    "project_id": PROJECT_ID,
                    "run_id": run_id,
                },
            )

            reconciliation_data = parse_result(reconciliation_result)

            assert reconciliation_data["success"] is True
            assert reconciliation_data["run_id"] == run_id

            conflicts = reconciliation_data.get("conflicts", [])

            print(f"Conflicts: {len(conflicts)}")

            # 6. List project runs
            print("\nCalling list_project_runs...")

            runs_result = await session.call_tool(
                "list_project_runs",
                {
                    "project_id": PROJECT_ID,
                },
            )

            runs_data = parse_result(runs_result)

            assert runs_data["success"] is True

            run_ids = {
                run["run_id"]
                for run in runs_data.get("runs", [])
            }

            assert run_id in run_ids

            print(f"Project runs: {len(run_ids)}")

            print("\nMCP integration test passed.")


if __name__ == "__main__":
    asyncio.run(main())