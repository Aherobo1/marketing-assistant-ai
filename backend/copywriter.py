"""
Copywriter module for the Marketing Assistant AI.
Core AI-powered content generation using a fine-tuned LLM.
"""

import os
import json
import httpx
from typing import Dict, List, Any, Optional, Tuple
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

import config
from brand_style import brand_style_manager
from vector_store import vector_store

class Copywriter:
    """Generates marketing copy using a fine-tuned LLM."""

    def __init__(self):
        """Initialize the Copywriter with Cohere LLM client."""
        self.model = "command"  # Cohere's generation model
        self.api_key = config.COHERE_API_KEY
        logger.info("Copywriter initialized with Cohere API successfully")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def generate_copy(
        self,
        prompt: str,
        content_type: Optional[str] = None,
        length: Optional[str] = None,
        include_cta: bool = False,
        reference_similar_content: bool = True,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Generate marketing copy based on the user prompt and parameters.
        Note: Removed tone parameter as we always use the established style
        """
        try:
            # Step 1: Format prompt with brand style guidelines
            branded_prompt = brand_style_manager.format_prompt_with_brand_style(prompt, content_type)

            # Step 2: Find similar content for reference (if enabled)
            reference_content = []
            if reference_similar_content:
                logger.info(f"Searching for similar content to reference for prompt: {prompt[:50]}...")
                search_results = await vector_store.search(prompt, top_k=3)
                if search_results:
                    reference_content = [result['text'] for result in search_results]
                    logger.info(f"Found {len(reference_content)} similar content items to reference")
                    for i, content in enumerate(reference_content):
                        logger.debug(f"Reference content {i+1}: {content[:100]}...")
                else:
                    logger.warning("No similar content found in vector store for reference")

            # Step 3: Add length and CTA instructions if needed
            if length:
                branded_prompt += f"\n- Generate {length} content"
            if include_cta:
                branded_prompt += "\n- Include a direct, empowering call to action"

            # Step 4: Add reference content if available
            if reference_content:
                branded_prompt += "\n\nReference these successful examples for tone and style:\n"
                branded_prompt += "\n---\n".join(reference_content)

            # Step 5: Generate content using the LLM
            generated_content = await self._call_llm_api(branded_prompt, max_tokens)

            # Step 6: Post-process to remove any mentions of Adriana James
            generated_content = self._remove_name_mentions(generated_content)

            # Step 7: Check content alignment with brand style
            alignment_check = brand_style_manager.check_content_alignment(generated_content)

            # Step 7: Generate alternative headline suggestions
            headline_suggestions = await self._generate_headline_suggestions(prompt, generated_content)

            # Step 8: Return the generated content with metadata
            result = {
                "content": generated_content,
                "suggestions": headline_suggestions,
                "metadata": {
                    "content_type": content_type,
                    "tone": None,  # Removed tone parameter
                    "alignment_score": alignment_check['alignment_score'],
                    "generated_at": None  # Will be added by the API
                }
            }

            # Add alignment issues if any
            if alignment_check['taboo_words_found'] or alignment_check['terminology_issues']:
                result["alignment_issues"] = {
                    "taboo_words_found": alignment_check['taboo_words_found'],
                    "terminology_issues": alignment_check['terminology_issues']
                }

            logger.info(f"Generated content with {len(generated_content)} characters")
            return result

        except Exception as e:
            logger.error(f"Error generating copy: {str(e)}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _call_llm_api(self, prompt: str, max_tokens: int = 1000) -> str:
        """
        Call the Cohere API to generate content.
        
        Args:
            prompt: The formatted prompt for the LLM
            max_tokens: Maximum tokens for the generated response
        
        Returns:
            Generated content as a string with preserved formatting
        """
        try:
            cohere_api_key = config.COHERE_API_KEY
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.cohere.ai/v1/generate",
                    headers={
                        "Authorization": f"Bearer {cohere_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "command",
                        "prompt": f"{prompt}\n\nNote: Please preserve formatting with proper paragraphs, line breaks, and bullet points where appropriate.",
                        "max_tokens": max_tokens,
                        "temperature": 0.7,
                        "k": 0,
                        "p": 0.75,
                        "return_likelihoods": "NONE"
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    generated_text = result["generations"][0]["text"].strip()
                    
                    # Preserve paragraph breaks and formatting
                    formatted_text = (
                        generated_text
                        .replace("\n\n", "<paragraph-break>")  # Preserve paragraph breaks
                        .replace("\n- ", "\n• ")  # Convert hyphens to bullets
                        .replace("<paragraph-break>", "\n\n")  # Restore paragraph breaks
                    )
                    
                    return formatted_text
                else:
                    logger.error(f"Cohere API error: {response.status_code}, {response.text}")
                    raise Exception(f"Cohere API error: {response.status_code}")
            
        except Exception as e:
            logger.error(f"Error calling Cohere API: {str(e)}")
            raise

    async def _generate_headline_suggestions(self, original_prompt: str, generated_content: str) -> List[str]:
        """
        Generate alternative headline suggestions based on the content.

        Args:
            original_prompt: The original user prompt
            generated_content: The generated marketing content

        Returns:
            List of headline suggestions
        """
        try:
            # Create a prompt for headline generation
            headline_prompt = f"""
            Generate 3 alternative marketing headlines for the following content.
            Make headlines compelling, concise, and aligned with the content's message.
            Each headline should be unique and capture attention.
            IMPORTANT: Do not mention any specific person's name in the headlines.

            ORIGINAL PROMPT:
            {original_prompt}

            CONTENT:
            {generated_content}

            Generate exactly 3 headlines, one per line, without numbering or prefixes.
            """

            # Call LLM to generate headlines
            response = await self._call_llm_api(
                prompt=headline_prompt,
                max_tokens=100  # Shorter limit for headlines
            )

            # Process the response into a list of headlines
            headlines = [
                headline.strip()
                for headline in response.split('\n')
                if headline.strip() and not headline.lower().startswith(('headline', 'title', '-', '*', '•'))
            ]

            # Remove any mentions of Adriana James from headlines
            headlines = [self._remove_name_mentions(headline) for headline in headlines]

            # Ensure we have exactly 3 headlines
            if len(headlines) > 3:
                headlines = headlines[:3]
            while len(headlines) < 3:
                headlines.append(f"Headline Option {len(headlines) + 1}")

            logger.info(f"Generated {len(headlines)} headline suggestions")
            return headlines

        except Exception as e:
            logger.error(f"Error generating headline suggestions: {str(e)}")
            # Return empty list instead of mock response on error
            return []

    async def improve_copy(self, content: str, feedback: str) -> str:
        """
        Improve content based on user feedback.

        Args:
            content: Original generated content
            feedback: User feedback for improvement

        Returns:
            Improved content
        """
        try:
            # Format prompt for improvement
            improve_prompt = f"""
            Please improve the following marketing content based on the feedback provided:
            IMPORTANT: Do not mention any specific person's name in the content.

            ORIGINAL CONTENT:
            {content}

            FEEDBACK:
            {feedback}

            IMPROVED CONTENT:
            """

            # Call LLM to improve content
            improved_content = await self._call_llm_api(improve_prompt, max_tokens=1200)

            # Remove any mentions of Adriana James from improved content
            improved_content = self._remove_name_mentions(improved_content)

            logger.info(f"Improved content based on feedback")
            return improved_content

        except Exception as e:
            logger.error(f"Error improving content: {str(e)}")
            raise

    async def analyze_content_performance(self, content: str) -> Dict[str, Any]:
        """
        Analyze marketing content for performance prediction.

        Args:
            content: Marketing content to analyze

        Returns:
            Dictionary with analysis results
        """
        try:
            # This would be enhanced with actual ML models in production
            # Simplified mock response for demonstration

            # Very basic analysis using length and keyword presence
            word_count = len(content.split())
            has_cta = any(phrase in content.lower() for phrase in ["call", "contact", "get started", "try", "buy", "sign up"])
            sentence_count = len([s for s in content.split(".") if s.strip()])
            avg_words_per_sentence = word_count / max(1, sentence_count)

            # Simple scoring system
            readability_score = 100 - min(100, max(0, abs(avg_words_per_sentence - 15) * 5))
            cta_score = 90 if has_cta else 60
            length_score = min(100, max(0, word_count / 3))

            overall_score = (readability_score + cta_score + length_score) / 3

            return {
                "overall_score": round(overall_score, 1),
                "readability_score": round(readability_score, 1),
                "cta_effectiveness": round(cta_score, 1),
                "length_appropriateness": round(length_score, 1),
                "metrics": {
                    "word_count": word_count,
                    "sentence_count": sentence_count,
                    "avg_words_per_sentence": round(avg_words_per_sentence, 1),
                    "has_cta": has_cta
                },
                "improvement_suggestions": [
                    "Consider adding a stronger call to action" if cta_score < 80 else "Your call to action is effective",
                    "Try to use shorter sentences for better readability" if avg_words_per_sentence > 20 else "Your sentence length is good for readability",
                    "Consider adding more content for better engagement" if word_count < 100 else "Your content length is appropriate"
                ]
            }

        except Exception as e:
            logger.error(f"Error analyzing content: {str(e)}")
            raise

    def _remove_name_mentions(self, content: str) -> str:
        """
        Remove any mentions of specific names from the generated content.

        Args:
            content: The generated content to process

        Returns:
            Content with name mentions removed
        """
        try:
            # Remove any mentions of "Adriana James" (case insensitive)
            import re
            pattern = re.compile(r'\bAdriana\s+James\b', re.IGNORECASE)
            content = pattern.sub('', content)

            # Clean up any double spaces that might result from the removal
            content = re.sub(r'\s+', ' ', content)

            # Clean up any lines that might now be empty
            content = '\n'.join([line for line in content.split('\n') if line.strip()])

            logger.info("Removed any name mentions from generated content")
            return content
        except Exception as e:
            logger.error(f"Error removing name mentions: {str(e)}")
            return content

# Create a singleton instance
copywriter = Copywriter()
