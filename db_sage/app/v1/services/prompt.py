import json
from fastapi import HTTPException, status

from db_sage.app.core.base.services import Service
from db_sage.app.core.config.embedder import DatabaseEmbedder
from db_sage.app.core.config.instruments import PostgresAgentInstruments
from db_sage.app.core.config import llm
from db_sage.app.utils.types import TurboTool
from db_sage.app.v1.responses.prompt import SqlQueryResultsResponse, SqlQueryResponseData


class PromptService(Service):
    def generate_and_run_sql(self, data):
        """
        Generates and executes an SQL query based on the provided prompt and table definitions.

        This method performs the following steps:
        1. Extracts the base prompt from the input `data`.
        2. Retrieves table definitions related to embeddings from the database.
        3. Utilizes the `DatabaseEmbedder` to find tables similar to the base prompt.
        4. Constructs a prompt that includes the relevant table definitions to be used for SQL query generation.
        5. Uses a language model (`llm`) to generate an SQL query from the constructed prompt.
        6. Executes the generated SQL query using a tool configured to run SQL.
        7. Validates the SQL execution process.
        8. Reads and processes the SQL query and its results.
        9. Constructs and returns a response containing the original prompt, the SQL query, and the query results.

        Args:
            data (PromptData): An object containing the prompt for which the SQL query needs to be generated.

        Returns:
            SqlQueryResultsResponse: A response object containing:
                - A message indicating successful SQL query generation.
                - An instance of `SqlQueryResponseData` with:
                    - `prompt`: The original prompt provided.
                    - `results`: The results of the SQL query execution.
                    - `sql`: The SQL query that was generated and executed.

        Raises:
            HTTPException: If no similar tables are found or other issues arise, an HTTP 400 error is raised indicating the need for existing tables.
        """
        with PostgresAgentInstruments("prompt-endpoint") as (agent_instruments, db):

            # ---------------- BUILDING TABLE DEFINITIONS ----------------

            base_prompt = data.prompt

            map_table_name_to_table_def = db.get_table_definition_map_for_embeddings()

            database_embedder = DatabaseEmbedder()

            for name, table_def in map_table_name_to_table_def.items():
                database_embedder.add_table(name, table_def)

            similar_tables = database_embedder.get_similar_tables(base_prompt, n=2)
            print("\n---------------- SIMILAR TABLES ---------------")
            print(similar_tables)

            if not similar_tables:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please provide existing tables query.")

            table_definitions = database_embedder.get_table_definitions_from_names(
                similar_tables
            )
            
            prompt = f"Fulfill this database query: {base_prompt}"
            prompt = llm.add_cap_ref(
                prompt,
                f"Use these TABLE_DEFINITIONS to satisfy the database query.",
                "TABLE_DEFINITIONS",
                table_definitions
            )

            # -------------------------------- AGENTS --------------------------------

            tools = [
                TurboTool("run_sql", llm.run_sql_tool_config, agent_instruments.run_sql)
            ]

            sql_response = llm.prompt(
                prompt,
                model="gpt-4o-mini",
                instructions="You are an elite SQL developer. You generate the most concise and performant SQL queries."
            )

            results_response = llm.prompt_func(
                "Use the run_sql function to run the SQL you have just generated: "
                + sql_response,
                model="gpt-4o-mini",
                instructions="You are an elite SQL developer. You generate the most concise and performant SQL queries.",
                turbo_tools=tools
            )

            agent_instruments.validate_run_sql()

            # -------------------------------- Read result files --------------------------------
            sql_query = open(agent_instruments.sql_query_file).read()
            sql_query_results = open(agent_instruments.run_sql_results_file).read()

            response_data = SqlQueryResponseData(
                prompt=base_prompt,
                results=json.loads(sql_query_results),
                sql=sql_query
            )

            response = SqlQueryResultsResponse(
                message="Successfully generated SQL Query.",
                data=response_data
            )
            return response

    def create(self):
        pass

    def fetch(self):
        pass

    def fetch_all(self):
        pass

    def update(self):
        pass

    def delete(self):
        pass

prompt_service = PromptService()