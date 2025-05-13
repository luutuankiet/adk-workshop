from google.api_core.exceptions import InvalidArgument
import json
import os
import asyncio
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timezone
from dotenv import load_dotenv

# Google Cloud imports
from google.cloud import firestore
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
from vertexai.language_models import TextEmbeddingModel
from google.cloud.firestore_v1.vector import Vector
load_dotenv()

@dataclass
class ProcessedChunk:
    url: str
    chunk_number: int
    content: str
    metadata: Dict[str, Any]
    embedding: List[float]

# def chunk_text(text: str, chunk_size: int = 5000) -> List[str]:
#     """Split text into chunks, respecting code blocks and paragraphs."""
#     chunks = []
#     start = 0
#     text_length = len(text)

#     while start < text_length:
#         # Calculate end position
#         end = start + chunk_size

#         # If we're at the end of the text, just take what's left
#         if end >= text_length:
#             chunks.append(text[start:].strip())
#             break

#         # Try to find a code block boundary first ()
#         chunk = text[start:end]
#         code_block = chunk.rfind('')
#         if code_block != -1 and code_block > chunk_size * 0.3:
#             end = start + code_block

#         # If no code block, try to break at a paragraph
#         elif '\n\n' in chunk:
#             # Find the last paragraph break
#             last_break = chunk.rfind('\n\n')
#             if last_break > chunk_size * 0.3:  # Only break if we're past 30% of chunk_size
#                 end = start + last_break

#         # If no paragraph break, try to break at a sentence
#         elif '. ' in chunk:
#             # Find the last sentence break
#             last_period = chunk.rfind('. ')
#             if last_period > chunk_size * 0.3:  # Only break if we're past 30% of chunk_size
#                 end = start + last_period + 1

#         # Extract chunk and clean it up
#         chunk = text[start:end].strip()
#         if chunk:
#             chunks.append(chunk)

#         # Move start position for next chunk
#         start = max(start + 1, end)

#     return chunks

async def get_embedding(text: str) -> List[float]:
    """Get embedding vector from Vertex AI."""
    try:
        # Create a synchronous function to call the embedding model
        def call_embedding_model():
            embeddings = embedding_model.get_embeddings([text])
            # embeddings = embedding_model.embed_documents([text])
            # return embeddings
            return embeddings[0].values
        
        # Run the synchronous function in a thread pool
        loop = asyncio.get_running_loop()
        embedding = await loop.run_in_executor(None, call_embedding_model)
        
        return embedding
    except InvalidArgument as e:
        print(f"Invalid argument error: {e}")
        # Return a zero vector with the same dimension as the model's output
        # Gecko model typically returns 768-dimensional embeddings
        # return [0.0] * 768
    except Exception as e:
        print(f"Error getting embedding from Vertex AI: {e}")
        # Return a zero vector with the same dimension as the model's output
        # Gecko model typically returns 768-dimensional embeddings
        return [0.0] * 768


async def insert_chunk(chunk: ProcessedChunk):
    """Insert a processed chunk into Firestore."""
    try:
        # Create a document ID based on URL and chunk number
        safe_url = chunk.url.replace("/", "_").replace(".", "_")
        doc_id = f"{safe_url}_{chunk.chunk_number}"
        
        # Convert the chunk to a dictionary for Firestore
        data = {
            "url": chunk.url,
            "content": chunk.content,
            "metadata": chunk.metadata,
            # Store embedding as a map of indices to values
            "embedding_map": Vector(chunk.embedding),
            # "embedding_map": {str(i): v for i, v in enumerate(chunk.embedding)},
            "created_at": firestore.SERVER_TIMESTAMP
        }
        
        # Add to Firestore
        collection_name = "gchat_messages_v2"
        doc_ref = db.collection(collection_name).document(doc_id)
        doc_ref.set(data)
        
        print(f"Inserted chunk {chunk.chunk_number} for {chunk.url}")
        return doc_id
    except Exception as e:
        print(f"Error inserting chunk into Firestore: {e}")
        return None

# Initialize Firestore client
db = firestore.Client(
    project='joon-sandbox',
    database='test-db'
)

# Initialize Vertex AI
# project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
# location = os.getenv("VERTEX_LOCATION", "us-central1")
project_id = "joon-sandbox"
location = "asia-southeast1"
vertexai.init(project=project_id, location=location)

# Initialize Gemini model
gemini_model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
gemini_model = GenerativeModel(gemini_model_name)

# Initialize embedding model
embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-005")

async def process_gchat_message(message: Dict[str, Any], msg_number: int) -> ProcessedChunk:
    """Process a single chat message."""
    # Combine relevant message fields for embedding
    # Get message text from formattedText field
    if not message.get('formattedText') and message.get('attachment'):
        message_text = message['attachment'][0]['contentName']
    else:
        message_text = message.get('formattedText', '')

    message_url = message.get('uri', '')
    
    # Get embedding
    embedding = await get_embedding(message_text)
    
    # Create metadata
    metadata = {
        "source": "google_chat",
        "timestamp": message.get('createTime'),
        "sender": message['sender']['name'],
        "sender": message['space']['name'],
    }
    
    return ProcessedChunk(
        url=message_url,  # Using message number as URL
        chunk_number=msg_number,
        content=message_text,
        metadata=metadata,
        embedding=embedding
    )

async def process_gchat_file(filepath: str):
    """Process the entire gchat.json file."""
    try:
        # Load JSON file
        with open(filepath, 'r', encoding='utf-8') as f:
            messages = json.load(f)
        
        print(f"Processing {len(messages)} messages from {filepath}")
        
        # Process messages in small batches (similar to original code)
        batch_size = 5
        for i in range(0, len(messages), batch_size):
            batch = messages[i:i+batch_size]
            
            # Process current batch
            tasks = [
                process_gchat_message(msg, i + j) 
                for j, msg in enumerate(batch)
            ]
            processed_chunks = await asyncio.gather(*tasks)
            
            # Store processed chunks
            insert_tasks = [
                insert_chunk(chunk) 
                for chunk in processed_chunks
            ]
            await asyncio.gather(*insert_tasks)
            
            # Progress update
            print(f"Processed messages {i} to {min(i+batch_size, len(messages))}")
            
            # Add delay between batches to respect rate limits
            if i + batch_size < len(messages):
                await asyncio.sleep(2)
    except FileNotFoundError:
        print(f"Error: Could not find file {filepath}")
    except json.JSONDecodeError:
        print(f"Error: {filepath} is not a valid JSON file")
    except Exception as e:
        print(f"Error processing file: {str(e)}")


async def main():
    filepath = "gchat.json"  # Adjust path as needed
    await process_gchat_file(filepath)

if __name__ == "__main__":
    asyncio.run(main())