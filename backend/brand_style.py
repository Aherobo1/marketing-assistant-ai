"""
Brand style module for the Marketing Assistant AI.
Ensures generated content aligns with Adriana James' brand voice and tone.
"""

import json
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
from loguru import logger

import config

class BrandStyleManager:
    """Manages brand style guidelines and ensures content consistency."""

    def __init__(self):
        """Initialize the BrandStyleManager with default or stored style guidelines."""
        self.style_path = Path(config.DATA_DIR) / "style_guidelines" / "brand_style.json"
        self.style_guidelines = self._load_or_create_style()
        self.content_formats = {
            "website_copy": """
                Generate engaging website copy for a brand or business.
                - Start with a strong headline and supporting subheadline
                - Write in a clear, benefit-driven tone
                - Use SEO-friendly keywords naturally
                - Structure content with short paragraphs and bullet points
                - Include a clear call-to-action at the end
            """,
            "email": """
                Create a marketing or sales email for a target audience.
                - Start with a compelling subject line
                - Use a warm, conversational tone
                - Keep the message focused and value-driven
                - Personalize where possible (name, context)
                - End with a clear and persuasive CTA
            """,
            "social_media": """
                Write social media content tailored to a specific platform.
                - Hook the reader within the first sentence
                - Keep the message concise and engaging
                - Use platform-appropriate tone and emojis (if applicable)
                - Add relevant hashtags and tag accounts when needed
                - Include a prompt or CTA to drive interaction
            """,
            "blog_post": """
                Generate a blog article on a given topic or keyword.
                - Begin with a strong hook or introduction
                - Organize content with subheadings and logical flow
                - Use examples, data, and storytelling
                - Optimize for SEO with keywords and meta description
                - Conclude with a summary or actionable insight
            """,
            "sales_copy": """
                Write persuasive sales copy for a product or service.
                - Lead with a strong value proposition
                - Address specific pain points and offer solutions
                - Highlight features, benefits, and outcomes
                - Include social proof (testimonials, stats, etc.)
                - End with a direct and compelling CTA
            """,
            "ad_copy": """
                Create short, punchy ad copy for digital or print campaigns.
                - Capture attention in the first line
                - Use emotional or benefit-driven language
                - Keep it brief and persuasive
                - Align copy with the target audience
                - Include a CTA or promotional message
            """,
            "video_script": """
                Generate a short video script for a marketing video.
                - Hook the viewer in the first few seconds
                - Introduce the problem and present the solution
                - Keep the tone conversational and natural
                - Include visual cues and on-screen text ideas
                - Wrap up with a strong CTA
            """,
            "case_study": """
                Write a case study that highlights a customer success story.
                - Start with a quick summary of the results
                - Describe the client and their initial problem
                - Explain how the product/service helped
                - Include measurable outcomes or metrics
                - End with a quote and a CTA to learn more
            """,
            "product_description": """
                Generate a product description that drives interest and conversions.
                - Begin with the most attractive benefit
                - Mention key features and what makes the product unique
                - Use sensory and persuasive language
                - Include important specs or FAQs
                - End with a micro-CTA (e.g., "Shop now", "View details")
            """,
            "landing_page": """
                Write copy for a focused landing page.
                - Use a bold, attention-grabbing headline
                - Describe the offer clearly and simply
                - Include supporting details that reinforce value
                - Remove distractions and focus on a single goal
                - Add a CTA above the fold and at the end
            """,
            "press_release": """
                Create a professional press release for an announcement.
                - Begin with a headline that summarizes the news
                - Use a journalistic tone and structure
                - Provide key facts in the first paragraph
                - Add quotes from relevant leaders or stakeholders
                - End with boilerplate company info and contact details
            """,
            "newsletter": """
                Write a newsletter update for subscribers.
                - Start with a warm greeting or short intro
                - Highlight the most important news or offer first
                - Use engaging sub-sections or article teasers
                - Maintain consistent tone with the brand
                - Include CTAs to drive clicks or traffic
            """
        }
        logger.info("BrandStyleManager initialized successfully")

    def _load_or_create_style(self) -> Dict[str, Any]:
        """Load existing style guidelines or create new ones with defaults."""
        try:
            if self.style_path.exists():
                with open(self.style_path, 'r') as f:
                    style = json.load(f)
                logger.info("Loaded existing brand style guidelines")
                return style
            else:
                # Create directory if it doesn't exist
                self.style_path.parent.mkdir(exist_ok=True)

                # Use default style guidelines
                style = config.DEFAULT_BRAND_STYLE

                # Save default style
                with open(self.style_path, 'w') as f:
                    json.dump(style, f, indent=2)

                logger.info("Created default brand style guidelines")
                return style
        except Exception as e:
            logger.error(f"Error loading or creating style guidelines: {str(e)}")
            # Fall back to default style
            return config.DEFAULT_BRAND_STYLE

    def get_style_guidelines(self) -> Dict[str, Any]:
        """
        Get current brand style guidelines.

        Returns:
            Dictionary of style guidelines
        """
        return self.style_guidelines

    def update_style_guidelines(self, new_style: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update brand style guidelines.

        Args:
            new_style: Dictionary with new style guidelines

        Returns:
            Updated style guidelines dictionary
        """
        try:
            # Merge new style with existing
            for key, value in new_style.items():
                self.style_guidelines[key] = value

            # Ensure brand name is preserved
            self.style_guidelines['brand_name'] = config.BRAND_NAME

            # Save updated style
            with open(self.style_path, 'w') as f:
                json.dump(self.style_guidelines, f, indent=2)

            logger.info("Updated brand style guidelines")
            return self.style_guidelines
        except Exception as e:
            logger.error(f"Error updating style guidelines: {str(e)}")
            raise

    def format_prompt_with_brand_style(self, user_prompt: str, content_type: Optional[str] = None) -> str:
        """Format user prompt to match the distinctive communication style."""

        style_instructions = [
            "Follow these distinctive communication style guidelines:",
            "- Use empowering, assertive language that inspires action",
            "- Address the reader directly using 'you' and 'your' with conviction",
            "- Create rhythmic, repetitive patterns in key messages for emphasis",
            "- Maintain a clear, confident, and conversational teaching tone",
            "- Use simple, practical language that communicates profound ideas",
            "- Use embedded commands (e.g., 'Decide now to change your thinking')",
            "- Include cause-effect statements (e.g., 'Because you understand this, you will now take action')",
            "- Speak with conviction and clarity rather than hesitation",
            "- Replace tentative phrases with confident declarations",
            "- Use a motivational coach-like clarity in all communications",
            "- IMPORTANT: Do not mention any specific person's name in the content"
        ]

        # Content type specific formatting
        content_format = self._get_content_format(content_type) if content_type else ""

        return "\n".join([
            f"Generate content based on this request:",
            f"\"{user_prompt}\"",
            "",
            "\n".join(style_instructions),
            content_format
        ])

    def check_content_alignment(self, content: str) -> Dict[str, Any]:
        """
        Check if generated content aligns with brand style guidelines.

        Args:
            content: Generated marketing content

        Returns:
            Dictionary with alignment metrics and suggestions
        """
        style = self.style_guidelines
        taboo_words = style.get('taboo_words', [])
        preferred_terms = style.get('preferred_terms', {})

        # Check for taboo words
        found_taboo_words = []
        for word in taboo_words:
            if word.lower() in content.lower():
                found_taboo_words.append(word)

        # Check for preferred terminology
        terminology_issues = []
        for avoid, use in preferred_terms.items():
            if avoid.lower() in content.lower():
                terminology_issues.append(f"Found '{avoid}', should use '{use}' instead")

        # Calculate an overall alignment score (simple implementation)
        issues_count = len(found_taboo_words) + len(terminology_issues)
        alignment_score = max(0, 100 - (issues_count * 10))  # Reduce score for each issue

        return {
            'alignment_score': alignment_score,
            'taboo_words_found': found_taboo_words,
            'terminology_issues': terminology_issues,
            'aligned': alignment_score >= 80  # Consider aligned if score is 80% or higher
        }

    def _get_content_format(self, content_type: str) -> str:
        """
        Get formatting instructions for specific content type.

        Args:
            content_type: Type of content to generate

        Returns:
            Formatting instructions as string
        """
        if not content_type:
            return ""

        format_instructions = self.content_formats.get(content_type, "")
        if format_instructions:
            return f"\nContent type specific instructions:\n{format_instructions.strip()}"
        return ""

# Create a singleton instance
brand_style_manager = BrandStyleManager()
