"""
Vector store module for the Marketing Assistant AI.
Uses FAISS for efficient storage and retrieval of content embeddings.
"""

import os
import json
import pickle
import faiss
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from loguru import logger
from datetime import datetime

import config
from embeddings import embeddings_manager

class VectorStore:
    """Manages vector database operations for content retrieval."""

    def __init__(self):
        """Initialize the VectorStore with FAISS index."""
        self.store_path = Path(config.VECTOR_DB_PATH)
        self.store_path.mkdir(exist_ok=True)

        self.index_path = self.store_path / "faiss_index.bin"
        self.metadata_path = self.store_path / "metadata.pkl"

        self.dimension = None
        self.index = None
        self.metadata = []

        self._load_or_create_index()
        logger.info("VectorStore initialized successfully")

        # Check if the index is empty and load sample data if needed
        if self.index.ntotal == 0:
            logger.warning("Vector store is empty. Loading sample data...")
            self._load_sample_data()

    def _load_or_create_index(self) -> None:
        """Load existing index or create new one if it doesn't exist."""
        try:
            if self.index_path.exists() and self.metadata_path.exists():
                # Load existing index and metadata
                self.index = faiss.read_index(str(self.index_path))
                with open(self.metadata_path, 'rb') as f:
                    self.metadata = pickle.load(f)
                self.dimension = self.index.d
                logger.info(f"Loaded existing vector index with {self.index.ntotal} vectors")
            else:
                # Default dimension for Cohere embeddings
                self.dimension = 1024
                self.index = faiss.IndexFlatL2(self.dimension)
                self.metadata = []
                logger.info(f"Created new vector index with dimension {self.dimension}")

                # Save the empty index and metadata
                self._save_index()
        except Exception as e:
            logger.error(f"Error loading or creating index: {str(e)}")
            raise

    def _save_index(self) -> None:
        """Save the index and metadata to disk."""
        try:
            faiss.write_index(self.index, str(self.index_path))
            with open(self.metadata_path, 'wb') as f:
                pickle.dump(self.metadata, f)
            logger.debug("Saved vector index and metadata")
        except Exception as e:
            logger.error(f"Error saving index: {str(e)}")
            raise

    async def add_documents(
        self,
        texts: List[str],
        metadata_list: Optional[List[Dict[str, Any]]] = None
    ) -> List[int]:
        """
        Add documents to the vector store.

        Args:
            texts: List of text documents to add
            metadata_list: List of metadata dictionaries for each document

        Returns:
            List of document IDs (vector indices)
        """
        try:
            if not texts:
                logger.warning("No texts provided to add to vector store")
                return []

            if metadata_list is None:
                metadata_list = [{} for _ in texts]

            if len(texts) != len(metadata_list):
                raise ValueError("Number of texts and metadata entries must match")

            # Generate embeddings
            embeddings = await embeddings_manager.get_embeddings(texts)

            # Check if embeddings match our dimension
            if embeddings.shape[1] != self.dimension:
                logger.warning(f"Embedding dimension mismatch: expected {self.dimension}, got {embeddings.shape[1]}")
                # If we have no documents yet, we can adapt to the new dimension
                if self.index.ntotal == 0:
                    self.dimension = embeddings.shape[1]
                    self.index = faiss.IndexFlatL2(self.dimension)
                    logger.info(f"Adapted to new dimension: {self.dimension}")
                else:
                    raise ValueError(f"Embedding dimension mismatch: expected {self.dimension}, got {embeddings.shape[1]}")

            # Add timestamp to metadata
            timestamp = datetime.now().isoformat()
            for meta in metadata_list:
                meta['timestamp'] = timestamp
                meta['document_id'] = len(self.metadata) + len(metadata_list)

            # Store texts in metadata
            for i, (text, meta) in enumerate(zip(texts, metadata_list)):
                meta['text'] = text

            # Add vectors to index
            start_idx = self.index.ntotal
            self.index.add(embeddings.astype(np.float32))
            self.metadata.extend(metadata_list)

            # Save updated index
            self._save_index()

            # Return document IDs
            doc_ids = list(range(start_idx, start_idx + len(texts)))
            logger.info(f"Added {len(texts)} documents to vector store")
            return doc_ids

        except Exception as e:
            logger.error(f"Error adding documents to vector store: {str(e)}")
            raise

    async def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        rerank: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents.

        Args:
            query: The search query
            top_k: Number of results to return
            filters: Dictionary of metadata filters
            rerank: Whether to use Cohere's reranking

        Returns:
            List of result dictionaries with document content and metadata
        """
        try:
            logger.info(f"Searching vector store with query: {query[:50]}... (top_k={top_k})")

            if self.index.ntotal == 0:
                logger.warning("Empty vector store, no results to return")
                return []

            logger.info(f"Vector store contains {self.index.ntotal} documents")

            # Generate query embedding
            query_embedding = await embeddings_manager.get_query_embedding(query)
            query_embedding = query_embedding.reshape(1, -1).astype(np.float32)

            # First pass: find more candidates than needed for reranking
            search_k = top_k * 3 if rerank else top_k
            search_k = min(search_k, self.index.ntotal)  # Don't request more than we have

            distances, indices = self.index.search(query_embedding, search_k)

            # Get metadata and texts for matching indices
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < 0 or idx >= len(self.metadata):
                    continue  # Skip invalid indices

                metadata = self.metadata[idx]
                text = metadata.get('text', '')

                # Apply filters if any
                if filters and not self._matches_filters(metadata, filters):
                    continue

                results.append({
                    'document_id': idx,
                    'text': text,
                    'metadata': {k: v for k, v in metadata.items() if k != 'text'},
                    'distance': float(distances[0][i])
                })

            # Apply reranking if requested
            if rerank and results:
                texts = [r['text'] for r in results]
                reranked = await embeddings_manager.rerank_results(query, texts, top_n=top_k)

                # Map reranked results back to our original results
                reranked_results = []
                for item in reranked:
                    orig_idx = item['index']
                    if 0 <= orig_idx < len(results):
                        reranked_results.append({
                            **results[orig_idx],
                            'relevance_score': item['relevance_score']
                        })

                results = reranked_results
            else:
                # Just take the top_k results
                results = results[:top_k]

            logger.info(f"Found {len(results)} matching documents for query")
            return results

        except Exception as e:
            logger.error(f"Error searching vector store: {str(e)}")
            raise

    def _matches_filters(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if metadata matches the specified filters."""
        for key, value in filters.items():
            if key not in metadata:
                return False

            if isinstance(value, list):
                # Check if metadata value is in the list
                if metadata[key] not in value:
                    return False
            elif metadata[key] != value:
                return False

        return True

    async def delete_document(self, document_id: int) -> bool:
        """
        Delete a document from the vector store.

        Args:
            document_id: ID of the document to delete

        Returns:
            Boolean indicating success
        """
        try:
            if document_id < 0 or document_id >= len(self.metadata):
                logger.warning(f"Invalid document ID: {document_id}")
                return False

            # FAISS doesn't support direct deletion, so we need to rebuild the index
            # Mark the document as deleted in metadata
            self.metadata[document_id]['deleted'] = True

            # Save updated metadata
            self._save_index()

            logger.info(f"Marked document {document_id} as deleted")
            return True

        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            raise

    async def get_document(self, document_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a document by ID.

        Args:
            document_id: ID of the document to retrieve

        Returns:
            Document with metadata or None if not found
        """
        try:
            if document_id < 0 or document_id >= len(self.metadata):
                logger.warning(f"Invalid document ID: {document_id}")
                return None

            metadata = self.metadata[document_id]

            # Check if document is marked as deleted
            if metadata.get('deleted', False):
                logger.warning(f"Document {document_id} is marked as deleted")
                return None

            text = metadata.get('text', '')

            return {
                'document_id': document_id,
                'text': text,
                'metadata': {k: v for k, v in metadata.items() if k != 'text' and k != 'deleted'}
            }

        except Exception as e:
            logger.error(f"Error retrieving document: {str(e)}")
            raise

    async def update_document(self, document_id: int, text: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update a document in the vector store.

        Args:
            document_id: ID of the document to update
            text: New document text
            metadata: New metadata (will be merged with existing)

        Returns:
            Boolean indicating success
        """
        try:
            if document_id < 0 or document_id >= len(self.metadata):
                logger.warning(f"Invalid document ID: {document_id}")
                return False

            # Get existing metadata
            existing_metadata = self.metadata[document_id]

            # Check if document is marked as deleted
            if existing_metadata.get('deleted', False):
                logger.warning(f"Cannot update deleted document {document_id}")
                return False

            # Generate new embedding
            embeddings = await embeddings_manager.get_embeddings([text])

            # Update the vector in the index
            faiss.IndexFlatL2_update_vectors(self.index, embeddings.astype(np.float32), np.array([document_id], dtype=np.int64))

            # Update metadata
            if metadata:
                for key, value in metadata.items():
                    existing_metadata[key] = value

            existing_metadata['text'] = text
            existing_metadata['updated_at'] = datetime.now().isoformat()

            # Save updated index
            self._save_index()

            logger.info(f"Updated document {document_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating document: {str(e)}")
            raise

    def _load_sample_data(self) -> None:
        """Load sample data from past campaigns into the vector store."""
        try:
            # Path to past campaigns directory
            campaigns_dir = Path(config.DATA_DIR) / "past_campaigns"

            if not campaigns_dir.exists() or not campaigns_dir.is_dir():
                logger.warning(f"Past campaigns directory not found: {campaigns_dir}")
                return

            # Find all JSON files in the directory
            campaign_files = list(campaigns_dir.glob("*.json"))
            if not campaign_files:
                logger.warning("No campaign files found in past_campaigns directory")
                return

            # Load and process each campaign file
            texts = []
            metadata_list = []

            for file_path in campaign_files:
                try:
                    with open(file_path, 'r') as f:
                        campaign_data = json.load(f)

                    # Extract content and metadata
                    if 'content' in campaign_data:
                        texts.append(campaign_data['content'])

                        # Create metadata entry
                        metadata = {
                            'content_type': campaign_data.get('content_type', 'unknown'),
                            'campaign_name': campaign_data.get('metadata', {}).get('campaign_name', file_path.stem),
                            'source': 'past_campaign',
                            'file_path': str(file_path)
                        }

                        # Add performance metrics if available
                        if 'metadata' in campaign_data and 'performance_metrics' in campaign_data['metadata']:
                            metadata['performance_metrics'] = campaign_data['metadata']['performance_metrics']

                        metadata_list.append(metadata)
                        logger.debug(f"Loaded campaign from {file_path.name}")
                except Exception as e:
                    logger.error(f"Error loading campaign file {file_path}: {str(e)}")
                    continue

            if not texts:
                logger.warning("No valid campaign content found in files")
                return

            # Add documents to vector store
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                doc_ids = loop.run_until_complete(self.add_documents(texts, metadata_list))
                logger.info(f"Added {len(doc_ids)} past campaigns to vector store")
            finally:
                loop.close()

        except Exception as e:
            logger.error(f"Error loading sample data: {str(e)}")

# Create a singleton instance
vector_store = VectorStore()