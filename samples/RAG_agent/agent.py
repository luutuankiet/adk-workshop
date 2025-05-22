# import google.cloud.logging

from google.cloud import firestore
from google.cloud.firestore_v1.vector import Vector
from google.cloud.firestore_v1.base_vector_query import DistanceMeasure

import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
from langchain_google_vertexai import VertexAIEmbeddings
from google.adk.agents import Agent
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters


# # Configure Cloud Logging
# logging_client = google.cloud.logging.Client()
# logging_client.setup_logging()
# logging.basicConfig(level=logging.INFO)

# Initializing the Firebase client
project_id = "joon-sandbox"
location = "asia-southeast1"
database_name = "test-db"

# Set up the Firestore client
db = firestore.Client(project=project_id, database=database_name)

# Initialize Vertex AI with explicit project and location
vertexai.init(project=project_id, location=location)

# TODO: Instantiate a collection reference
collection = db.collection("gchat_messages_v2")

# TODO: Instantiate an embedding model here
embedding_model = VertexAIEmbeddings(model_name="text-embedding-005")

# TODO: Instantiate a Generative AI model here
gen_model = model = GenerativeModel(
    model_name="gemini-1.5-pro",
    generation_config=GenerationConfig(temperature=0))

def search_vector_database(query: str) -> list:
    # For debugging - check if collection has documents
    all_docs = list(collection.limit(3).stream())
    # print(f"Collection has {len(all_docs)} documents")
    if not all_docs:
        return ["No documents found in the collection."]

    # 1. Generate the embedding of the query using the same model as data loading
    try:

        query_embedding = embedding_model.embed_query(query)

        # Create a Vector object from the embedding values
        query_vector = Vector(query_embedding)

        # 2. Get the 5 nearest neighbors
        vector_query = collection.find_nearest(
            vector_field="embedding_map",
            query_vector=query_vector,  # Use Vector object, not dictionary
            distance_measure=DistanceMeasure.EUCLIDEAN,
            limit=5,
        )

        # 3. Process results
        docs = list(vector_query.stream())  # Convert to list to avoid stream consumption issues
        print(f"Vector query returned {len(docs)} documents")

        if not docs:
            return ["No relevant documents found for your query."]

        # Extract content from documents
        context = [
            {
                "content": result.to_dict().get('content', ''),
                "url": result.to_dict().get('url', '')
                }
            for result in docs
            ]
        # context_str = "\n\n".join(context)

    except Exception as e:
        print(f"Error in vector search: {e}")
        context = f"Error performing vector search: {str(e)}"
        # context_str = f"Error performing vector search: {str(e)}"

    # Don't delete this logging statement.
    # logging.info(
    #     context_str, extra={"labels": {"service": "joon-service", "component": "context"}}
    # )
    return context
    # return context_str


async def mcp_filesystem():
    return await MCPToolset.from_server(
        connection_params=StdioServerParameters(
            command='npx',
            args=[
                "-y",
                "@modelcontextprotocol/server-filesystem",
                '/workspaces/EVERYTHING/joons/genai/google-chat-rag'
            ]

        )
    )

async def create_agent():
    tools, exit_stack = await mcp_filesystem()
    root_agent = Agent(
        name="system_activity_agent",
        model="gemini-1.5-pro",
        description=(
            "Retrivial agent that helps user find related discussions and issues from previous incidents in their documents."
        ),
    #     instruction=(
    #         """ 
    # **ROLE:**
    # You are a retrieval assistant designed to help users answer questions using only trusted, context-relevant information retrieved from a vector database.

    # **REQUIRED BEHAVIOR:**

    # 1. **Mandatory First Step:**

    #    * Always begin by calling the `search_vector_database` tool using a concise summary of the user’s question.
    #    * This step is required *before* any answer attempt.

    # 2. **Restricted Source:**

    #    * You are only allowed to answer questions using the content returned by `search_vector_database`.
    #    * Do **not** use any external knowledge, memory, or assumptions.

    # 3. **No Answer Case:**

    #    * If none of the returned documents directly relate to the question, respond:

    #      ```
    #      I cannot find specific information about this in the available messages.
    #      ```

    # 4. **Citation and Reasoning:**

    #    * Reference the retrieved content explicitly, quoting or summarizing the relevant passage(s).
    #    * This is used to help the user comprehend the documents so that they can onboard the team.
    #    * Guide the user through your thought process, explaining:
    #      * Why the retrieved info answers (or doesn’t answer) the question
    #      * What part of the context was most relevant
    #      * Include the **original source URL or ID** of the content for verification
    #    * Include additional document from the retrieved info that the user might want to explore, for the purpose of having an overview what info is available for their query.

    # 5. **Answer Format:**

    #    * Begin with a direct answer (if available from context)
    #    * Follow with a short explanation of how you found the answer from the retrieved messages.
    #    * Close with the citation (e.g. `"Source: [doc-title](url)"`)

    #     """
    #     ),
        tools=[*tools, search_vector_database],
        # tools=[search_vector_database,tool],
        )
    
    return root_agent, exit_stack

# # Test both functions
# def test_search():
#     result = search_vector_database("workflow")
#     print(f"Search result: {result[:200]}...")  # First 200 chars

prompt = ("do you have any idea on why there are some data in looker_extraction.history (for history system activity) that have no connection_id ?")
def test_complete_response():
    result = ask_gemini(prompt)
    print(f"Complete response: {result}")

root_agent = create_agent()
# # Run tests
# # test_search()
# test_complete_response()
