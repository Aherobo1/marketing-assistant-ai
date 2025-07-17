"""
Embeddings module for the Marketing Assistant AI.
Uses Cohere to generate and manage text embeddings.
"""

import cohere
from typing import List, Dict, Any, Optional
import numpy as np
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

import config

class EmbeddingsManager:
    """Manages the generation and manipulation of text embeddings using Cohere."""
    
    def __init__(self):
        """Initialize the EmbeddingsManager with Cohere API client."""
        try:
            self.co = cohere.Client(config.COHERE_API_KEY)
            logger.info("EmbeddingsManager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize EmbeddingsManager: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def get_embeddings(self, texts: List[str], model: str = "embed-english-v3.0") -> np.ndarray:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings to embed
            model: Cohere embedding model to use
            
        Returns:
            numpy.ndarray: Array of embeddings vectors
        """
        try:
            if not texts:
                logger.warning("Empty text list provided for embedding")
                return np.array([])
            
            # Ensure texts are not too long for the API
            processed_texts = [text[:8192] for text in texts]
            
            response = self.co.embed(
                texts=processed_texts,
                model=model,
                input_type="search_document"
            )
            
            embeddings = np.array(response.embeddings)
            logger.debug(f"Generated {len(embeddings)} embeddings with shape {embeddings.shape}")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def get_query_embedding(self, text: str, model: str = "embed-english-v3.0") -> np.ndarray:
        """
        Generate embedding for a single query text.
        
        Args:
            text: The query text to embed
            model: Cohere embedding model to use
            
        Returns:
            numpy.ndarray: Embedding vector for the query
        """
        try:
            response = self.co.embed(
                texts=[text[:8192]],
                model=model,
                input_type="search_query"
            )
            
            embedding = np.array(response.embeddings[0])
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating query embedding: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def rerank_results(
        self, 
        query: str, 
        documents: List[str], 
        model: str = "rerank-v3.5",
        top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Rerank documents based on relevance to the query.
        
        Args:
            query: The search query
            documents: List of documents to rerank
            model: Cohere reranking model to use
            top_n: Number of top results to return
            
        Returns:
            List of dictionaries with document index and relevance score
        """
        try:
            if not documents:
                logger.warning("Empty document list provided for reranking")
                return []
            
            # Truncate documents if they're too long
            processed_docs = [doc[:8192] for doc in documents]
            
            response = self.co.rerank(
                query=query,
                documents=processed_docs,
                model=model,
                top_n=min(top_n, len(processed_docs))
            )
            
            results = [
                {
                    "index": result.index,
                    "document": documents[result.index],
                    "relevance_score": result.relevance_score
                }
                for result in response.results
            ]
            
            logger.debug(f"Reranked {len(documents)} documents, returning top {len(results)}")
            return results
            
        except Exception as e:
            logger.error(f"Error reranking documents: {str(e)}")
            raise

# Create a singleton instance
embeddings_manager = EmbeddingsManager()