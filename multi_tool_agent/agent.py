# import google.cloud.logging

from google.cloud import firestore
from google.cloud.firestore_v1.vector import Vector
from google.cloud.firestore_v1.base_vector_query import DistanceMeasure

import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
from langchain_google_vertexai import VertexAIEmbeddings
from google.adk.agents import Agent

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

def search_vector_database(query: str):
    # For debugging - check if collection has documents
    all_docs = list(collection.limit(3).stream())
    print(f"Collection has {len(all_docs)} documents")
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
        context = [result.to_dict().get('content', '') for result in docs]
        context_str = "\n\n".join(context)

    except Exception as e:
        print(f"Error in vector search: {e}")
        context_str = f"Error performing vector search: {str(e)}"

    # Don't delete this logging statement.
    # logging.info(
    #     context_str, extra={"labels": {"service": "joon-service", "component": "context"}}
    # )
    return context_str

# TODO: Implement this function to pass Gemini the context data,
# generate a response, and return the response text.
def ask_gemini(question: str) -> str:

    # 1. Create a prompt_template with instructions to the model
    # to use provided context info to answer the question.

    prompt_template = """
    You are an AI assistant specialized in Looker System Activity analysis.
    
    IMPORTANT INSTRUCTIONS:
    1. ONLY use the provided context to answer the question
    2. If the context doesn't contain relevant information, say "I cannot find specific information about this in the available messages"
    3. Cite specific parts of the context in your answer
    4. Do not make assumptions or inferences beyond what's explicitly stated in the context
    5. Format your response as follows:
        - Answer: [your response based strictly on context]
        - Source Messages: [quote relevant parts of context]
    
    Context from chat messages:
    {context}

    Question: {question}
    
    Response (remember to only use information from the context above):
    """

    # 2. Use your search_vector_database function to retrieve context
    # relevant to the question.
    context = search_vector_database(question)

    # 3. Format the prompt template with the question & context
    prompt = prompt_template.format(context=context, question=question)

    # 4. Pass the complete prompt template to gemini and get the text
    # of its response to return below.
    try:
        response = gen_model.generate_content(prompt)
        return str(response.text)  # Explicitly convert to string
    except Exception as e:
        return f"Error generating response: {str(e)}"


root_agent = Agent(
    name="system_activity_agent",
    model="gemini-1.5-pro",
    description=(
        "Agent to answer questions about Looker's System Activity of ONE instance."
    ),
    instruction=(
        """
    You are an AI assistant specialized in Looker System Activity analysis.
    
    IMPORTANT INSTRUCTIONS:
    0. **MUST USE TOOLS.** always use ask_gemini to get relevant context before answering.
    1. ONLY use the provided context to answer the question
    2. If the context doesn't contain relevant information, say "I cannot find specific information about this in the available messages"
    3. Cite specific parts of the context in your answer
    4. Do not make assumptions or inferences beyond what's explicitly stated in the context
    5. Format your response as follows:
        - Answer: [your response based strictly on context]
        - Source Messages: [quote relevant parts of context]
    """
    ),
    tools=[ask_gemini],
    )

# # Test both functions
# def test_search():
#     result = search_vector_database("workflow")
#     print(f"Search result: {result[:200]}...")  # First 200 chars

prompt = ("do you have any idea on why there are some data in looker_extraction.history (for history system activity) that have no connection_id ?")
def test_complete_response():
    result = ask_gemini(prompt)
    print(f"Complete response: {result}")

# # Run tests
# # test_search()
test_complete_response()