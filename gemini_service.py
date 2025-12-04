"""Google Gemini API service with FileSearch RAG support."""

from __future__ import annotations

import os
import time
import logging
from typing import Optional, List, Dict, Any, Generator
from pathlib import Path

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

# Global state
_client: Optional[genai.Client] = None
_rag_store_name: Optional[str] = None


def initialize_client() -> Optional[genai.Client]:
    """Initialize the Gemini client with API key."""
    global _client
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY not configured")
        return None
    _client = genai.Client(api_key=api_key)
    logger.info("Gemini client initialized")
    return _client


def get_client() -> Optional[genai.Client]:
    """Get the initialized Gemini client."""
    global _client
    if _client is None:
        return initialize_client()
    return _client


def create_rag_store(display_name: str) -> str:
    """Create a new FileSearch RAG store."""
    client = get_client()
    if not client:
        raise RuntimeError("Gemini client not initialized")

    store = client.file_search_stores.create(
        config=types.CreateFileSearchStoreConfig(display_name=display_name)
    )
    if not store.name:
        raise RuntimeError("Failed to create RAG store: name is missing")

    logger.info(f"Created RAG store: {store.name}")
    return store.name


def upload_file_to_rag_store(rag_store_name: str, file_path: str) -> None:
    """Upload a file to the RAG store with polling for completion."""
    client = get_client()
    if not client:
        raise RuntimeError("Gemini client not initialized")

    # Determine mime type based on extension
    ext = Path(file_path).suffix.lower()
    mime_types = {
        ".md": "text/markdown",
        ".txt": "text/plain",
        ".pdf": "application/pdf",
        ".html": "text/html",
        ".json": "application/json",
    }
    mime_type = mime_types.get(ext, "text/plain")

    # Upload file to RAG store
    with open(file_path, "rb") as f:
        operation = client.file_search_stores.upload_to_file_search_store(
            file_search_store_name=rag_store_name,
            file=f,
            config=types.UploadToFileSearchStoreConfig(mime_type=mime_type)
        )

    # Poll for completion
    while not operation.done:
        time.sleep(3)
        operation = client.operations.get(operation=operation)

    logger.info(f"Uploaded {file_path} to RAG store {rag_store_name}")


def initialize_rag_store(display_name: str = "TaoyuanYouthBureauKB") -> str:
    """Initialize RAG store and upload default documents."""
    global _rag_store_name

    # Check if we have a persisted store name
    persisted_name = os.getenv("RAG_STORE_NAME")
    if persisted_name:
        _rag_store_name = persisted_name
        logger.info(f"Using existing RAG store: {_rag_store_name}")
        return _rag_store_name

    # Create new store
    _rag_store_name = create_rag_store(display_name)

    # Upload default files from rag_data/
    rag_data_dir = os.getenv("RAG_DATA_DIR", "rag_data")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    rag_path = Path(base_dir) / rag_data_dir

    if rag_path.exists():
        md_files = list(rag_path.glob("*.md"))
        logger.info(f"Found {len(md_files)} markdown files in {rag_path}")
        for md_file in md_files:
            try:
                upload_file_to_rag_store(_rag_store_name, str(md_file))
            except Exception as e:
                logger.error(f"Failed to upload {md_file}: {e}")
    else:
        logger.warning(f"RAG data directory not found: {rag_path}")

    logger.info(f"RAG store initialized: {_rag_store_name}")
    return _rag_store_name


def get_rag_store_name() -> Optional[str]:
    """Get the current RAG store name."""
    return _rag_store_name


def delete_rag_store(rag_store_name: Optional[str] = None) -> None:
    """Delete the RAG store."""
    client = get_client()
    if not client:
        raise RuntimeError("Gemini client not initialized")

    store_name = rag_store_name or _rag_store_name
    if not store_name:
        logger.warning("No RAG store to delete")
        return

    client.file_search_stores.delete(
        name=store_name,
        config={"force": True}
    )
    logger.info(f"Deleted RAG store: {store_name}")


def generate_with_rag_stream(
    query: str,
    system_prompt: str,
    chat_history: List[Dict[str, str]],
    model: str = "gemini-2.5-flash"
) -> Generator[Dict[str, Any], None, None]:
    """
    Stream content generation using RAG FileSearch.

    Args:
        query: User's question
        system_prompt: System instruction for the chatbot
        chat_history: Previous messages in the conversation
        model: Gemini model to use

    Yields:
        Dict with 'type' ('text', 'sources', 'end') and 'content'
    """
    client = get_client()
    if not client:
        raise RuntimeError("Gemini client not initialized")

    rag_store = get_rag_store_name()
    if not rag_store:
        raise RuntimeError("RAG store not initialized")

    # Build contents from chat history
    contents = []
    for msg in chat_history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(types.Content(
            role=role,
            parts=[types.Part.from_text(text=msg["content"])]
        ))

    # Add current query
    contents.append(types.Content(
        role="user",
        parts=[types.Part.from_text(text=query)]
    ))

    # Configure with FileSearch tool and system instruction
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        tools=[types.Tool(
            file_search=types.FileSearch(
                file_search_store_names=[rag_store]
            )
        )]
    )

    # Stream response
    grounding_chunks = []

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=config
    ):
        if chunk.text:
            yield {"type": "text", "content": chunk.text}

        # Capture grounding metadata (usually in final chunk)
        if chunk.candidates and len(chunk.candidates) > 0:
            candidate = chunk.candidates[0]
            if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                if hasattr(candidate.grounding_metadata, 'grounding_chunks') and candidate.grounding_metadata.grounding_chunks:
                    grounding_chunks = candidate.grounding_metadata.grounding_chunks

    # Yield grounding chunks at the end
    if grounding_chunks:
        sources = []
        for gc in grounding_chunks:
            if hasattr(gc, 'retrieved_context') and gc.retrieved_context:
                if hasattr(gc.retrieved_context, 'text') and gc.retrieved_context.text:
                    sources.append({"text": gc.retrieved_context.text})
        if sources:
            yield {"type": "sources", "content": sources}

    yield {"type": "end", "content": ""}


def generate_with_rag(
    query: str,
    system_prompt: str,
    chat_history: List[Dict[str, str]],
    model: str = "gemini-2.5-flash"
) -> Dict[str, Any]:
    """
    Non-streaming content generation using RAG FileSearch.

    Returns:
        Dict with 'text' and 'sources' keys
    """
    client = get_client()
    if not client:
        raise RuntimeError("Gemini client not initialized")

    rag_store = get_rag_store_name()
    if not rag_store:
        raise RuntimeError("RAG store not initialized")

    # Build contents from chat history
    contents = []
    for msg in chat_history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(types.Content(
            role=role,
            parts=[types.Part.from_text(text=msg["content"])]
        ))

    # Add current query
    contents.append(types.Content(
        role="user",
        parts=[types.Part.from_text(text=query)]
    ))

    # Configure with FileSearch tool and system instruction
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        tools=[types.Tool(
            file_search=types.FileSearch(
                file_search_store_names=[rag_store]
            )
        )]
    )

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=config
    )

    # Extract grounding chunks
    sources = []
    if response.candidates and len(response.candidates) > 0:
        candidate = response.candidates[0]
        if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
            if hasattr(candidate.grounding_metadata, 'grounding_chunks') and candidate.grounding_metadata.grounding_chunks:
                for gc in candidate.grounding_metadata.grounding_chunks:
                    if hasattr(gc, 'retrieved_context') and gc.retrieved_context:
                        if hasattr(gc.retrieved_context, 'text') and gc.retrieved_context.text:
                            sources.append({"text": gc.retrieved_context.text})

    return {
        "text": response.text or "",
        "sources": sources
    }
