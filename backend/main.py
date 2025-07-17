"""
Main FastAPI application for the Marketing Assistant AI.
Provides API endpoints for generating and managing marketing content.
"""

import os
import json
import glob
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends, Query, Body, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy import select, desc, func
from sqlalchemy.sql import Select

import config
from copywriter import copywriter
from vector_store import vector_store
from brand_style import brand_style_manager
from embeddings import embeddings_manager
from models import database, training_data

# Initialize logging
logger.add(config.LOG_FILE, level=config.LOG_LEVEL, rotation="10 MB", retention="1 month")

# Create FastAPI app
app = FastAPI(
    title="Marketing Assistant AI",
    description="AI-powered tool for marketing copywriting with Adriana James' brand voice",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define request and response models
class GenerateCopyRequest(BaseModel):
    prompt: str = Field(..., description="The main instruction for generating content")
    content_type: Optional[str] = Field(None, description="Type of content to generate")
    length: Optional[str] = Field(None, description="Desired length of the content")
    include_cta: Optional[bool] = Field(False, description="Whether to include a call to action")
    reference_similar_content: Optional[bool] = Field(True, description="Whether to reference similar content")
    max_tokens: Optional[int] = Field(1000, description="Maximum tokens for the generated response")

class TrainingDataRequest(BaseModel):
    content_type: str = Field(..., description="Type of content")
    content: str = Field(..., description="The marketing content")
    metadata: Optional[Dict[str, Any]] = Field({}, description="Additional metadata about the content")

class BrandStyleUpdateRequest(BaseModel):
    tone: Optional[List[str]] = Field(None, description="Brand tone options")
    voice_characteristics: Optional[List[str]] = Field(None, description="Voice characteristics")
    taboo_words: Optional[List[str]] = Field(None, description="Words to avoid")
    preferred_terms: Optional[Dict[str, str]] = Field(None, description="Preferred terminology")

class ContentImprovementRequest(BaseModel):
    content: str = Field(..., description="Original generated content")
    feedback: str = Field(..., description="User feedback for improvement")

# API Routes
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Marketing Assistant AI",
        "version": "1.0.0",
        "description": f"AI-powered marketing copywriter for {config.BRAND_NAME}"
    }

@app.post("/generate-copy")
async def generate_copy(request: GenerateCopyRequest):
    """Generate marketing copy based on the provided prompt and parameters."""
    try:
        # Validate content type if provided
        if request.content_type and request.content_type not in config.CONTENT_TYPES:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "status": "error",
                    "message": f"Invalid content_type. Must be one of: {', '.join(config.CONTENT_TYPES)}"
                }
            )
        
        # Generate copy
        result = await copywriter.generate_copy(
            prompt=request.prompt,
            content_type=request.content_type,
            length=request.length,
            include_cta=request.include_cta,
            reference_similar_content=request.reference_similar_content,
            max_tokens=request.max_tokens
        )
        
        # Add timestamp
        result["metadata"]["generated_at"] = datetime.now().isoformat()
        
        # Store the generated content in the vector store for future reference
        if result["content"]:
            metadata = {
                "content_type": request.content_type,
                "prompt": request.prompt,
                "generated": True
            }
            await vector_store.add_documents([result["content"]], [metadata])
        
        # Store the user query for future training
        query_path = Path(config.DATA_DIR) / "user_queries" / f"{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
        with open(query_path, 'w') as f:
            json.dump({
                "prompt": request.prompt,
                "parameters": {
                    "content_type": request.content_type,
                    "length": request.length,
                    "include_cta": request.include_cta
                },
                "timestamp": datetime.now().isoformat()
            }, f, indent=2)
        
        return {
            "status": "success",
            "content": result["content"],
            "suggestions": result.get("suggestions", []),
            "metadata": result["metadata"]
        }
        
    except Exception as e:
        logger.error(f"Error generating copy: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate copy: {str(e)}"
        )

@app.get("/brand-style")
async def get_brand_style():
    """Get the current brand style guidelines."""
    try:
        style = brand_style_manager.get_style_guidelines()
        return style
    except Exception as e:
        logger.error(f"Error getting brand style: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get brand style: {str(e)}"
        )

@app.put("/brand-style")
async def update_brand_style(request: BrandStyleUpdateRequest):
    """Update the brand style guidelines."""
    try:
        update_data = request.dict(exclude_unset=True)
        updated_style = brand_style_manager.update_style_guidelines(update_data)
        
        return {
            "status": "success",
            "message": "Brand style updated successfully",
            "style": updated_style
        }
    except Exception as e:
        logger.error(f"Error updating brand style: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update brand style: {str(e)}"
        )

@app.post("/training-data")
async def add_training_data(request: TrainingDataRequest):
    """Add new marketing content for AI training."""
    try:
        # Validate content type
        if request.content_type not in config.CONTENT_TYPES:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "status": "error",
                    "message": f"Invalid content_type. Must be one of: {', '.join(config.CONTENT_TYPES)}"
                }
            )
        
        # Prepare metadata
        metadata = request.metadata.copy()
        metadata["content_type"] = request.content_type
        metadata["added_at"] = datetime.now().isoformat()
        metadata["training_data"] = True
        
        # Add to database
        query = training_data.insert().values(
            content=request.content,
            content_type=request.content_type,
            metadata=metadata,
            added_at=datetime.now(),
            is_training_data=True
        )
        data_id = await database.execute(query)
        
        # Add to vector store for search functionality
        doc_ids = await vector_store.add_documents([request.content], [metadata])
        
        return {
            "status": "success",
            "message": "Training data added successfully",
            "data_id": data_id
        }
    except Exception as e:
        logger.error(f"Error adding training data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add training data: {str(e)}"
        )

@app.get("/training-data")
async def list_training_data(
    content_type: Optional[str] = Query(None, description="Filter by content type"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page")
):
    """Retrieve a list of available training data."""
    try:
        # Build base query
        base_query = select(training_data).where(training_data.c.is_training_data == True)
        
        if content_type:
            if content_type not in config.CONTENT_TYPES:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "status": "error",
                        "message": f"Invalid content_type. Must be one of: {', '.join(config.CONTENT_TYPES)}"
                    }
                )
            base_query = base_query.where(training_data.c.content_type == content_type)
        
        # Count total records
        count_query = select(func.count()).select_from(training_data).where(training_data.c.is_training_data == True)
        if content_type:
            count_query = count_query.where(training_data.c.content_type == content_type)
        total = await database.fetch_val(count_query)
        
        # Add pagination
        query = base_query.order_by(training_data.c.added_at.desc()) \
                         .offset((page - 1) * limit) \
                         .limit(limit)
        
        # Execute query
        records = await database.fetch_all(query)
        
        # Format response
        items = []
        for record in records:
            preview = record["content"][:100] + "..." if len(record["content"]) > 100 else record["content"]
            items.append({
                "id": record["id"],
                "content_type": record["content_type"],
                "preview": preview,
                "added_at": record["added_at"].isoformat()
            })
        
        return {
            "items": items,
            "pagination": {
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit
            }
        }
    except Exception as e:
        logger.error(f"Error listing training data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list training data: {str(e)}"
        )

@app.get("/training-data/{data_id}")
async def get_training_data(data_id: int):
    """Retrieve a specific training document by ID."""
    try:
        query = select([training_data]).where(training_data.c.id == data_id)
        record = await database.fetch_one(query)
        
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with ID {data_id} not found"
            )
        
        return {
            "id": record["id"],
            "content": record["content"],
            "content_type": record["content_type"],
            "metadata": record["metadata"],
            "added_at": record["added_at"].isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving training data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve training data: {str(e)}"
        )

@app.delete("/training-data/{data_id}")
async def delete_training_data(data_id: int):
    """Delete a specific training document by ID."""
    try:
        query = training_data.delete().where(training_data.c.id == data_id)
        result = await database.execute(query)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with ID {data_id} not found or could not be deleted"
            )
        
        # Also remove from vector store
        await vector_store.delete_document(data_id)
        
        return {
            "status": "success",
            "message": f"Document with ID {data_id} successfully deleted"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting training data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete training data: {str(e)}"
        )

@app.post("/improve-content")
async def improve_content(request: ContentImprovementRequest):
    """Improve content based on user feedback."""
    try:
        improved_content = await copywriter.improve_copy(
            content=request.content,
            feedback=request.feedback
        )
        
        return {
            "status": "success",
            "original_content": request.content,
            "improved_content": improved_content,
            "feedback": request.feedback
        }
    except Exception as e:
        logger.error(f"Error improving content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to improve content: {str(e)}"
        )

@app.post("/analyze-content")
async def analyze_content(content: str = Body(..., embed=True)):
    """Analyze marketing content for performance prediction."""
    try:
        analysis = await copywriter.analyze_content_performance(content)
        
        return {
            "status": "success",
            "analysis": analysis
        }
    except Exception as e:
        logger.error(f"Error analyzing content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze content: {str(e)}"
        )

@app.get("/user-queries")
async def list_user_queries(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page")
):
    """List user queries with pagination."""
    try:
        # Calculate offset
        offset = (page - 1) * limit
        
        # Get files from user_queries directory
        query_dir = Path(config.DATA_DIR) / "user_queries"
        query_dir.mkdir(exist_ok=True)
        
        # List all JSON files and sort by name (timestamp) in descending order
        files = sorted(query_dir.glob("*.json"), reverse=True)
        total = len(files)
        
        # Apply pagination
        files = files[offset:offset + limit]
        
        items = []
        for file in files:
            with open(file, 'r') as f:
                query_data = json.load(f)
                items.append(query_data)
        
        return {
            "items": items,
            "pagination": {
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit
            }
        }
    except Exception as e:
        logger.error(f"Error listing user queries: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list user queries: {str(e)}"
        )

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=True
    )
