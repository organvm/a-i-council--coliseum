"""
NLP Processing Module

Provides natural language processing capabilities for AI agents.
"""

import os
import json
import re
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from openai import AsyncOpenAI

# Configure logging
logger = logging.getLogger(__name__)

class NLPProcessor:
    """
    Natural Language Processing module for agent text understanding
    and generation.
    """
    
    def __init__(self, model_name: str = "gpt-4-turbo-preview"):
        self.model_name = model_name
        self.api_key = os.getenv("OPENAI_API_KEY")
        if self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("OPENAI_API_KEY not found. NLP features will use placeholders.")
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text
        
        Returns:
            Dict with sentiment label and score
        """
        # Placeholder for actual sentiment analysis
        return {
            "sentiment": "neutral",
            "score": 0.5,
            "confidence": 0.8
        }
    
    async def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract named entities from text
        
        Returns:
            List of entities with type and text
        """
        if not self.client:
            # Fallback heuristic: Extract capitalized words as potential entities
            # This is a basic fallback to support operation without an API key
            entities = []
            # Find capitalized words (single or consecutive)
            # We skip the first word if it looks like a sentence start,
            # but that's hard to distinguish without more context.
            # Here we just grab all capitalized sequences that aren't at the very start
            # or we accept some noise.

            # Regex to match sequences of capitalized words
            pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'

            for match in re.finditer(pattern, text):
                entity_text = match.group()
                # Skip if it's the first word of the text and single word (heuristic for sentence start)
                if match.start() == 0 and ' ' not in entity_text:
                    continue

                entities.append({
                    "text": entity_text,
                    "type": "UNKNOWN",
                    "start": match.start(),
                    "end": match.end(),
                    "confidence": 0.4
                })
            return entities

        prompt = f"""
        Extract named entities from the following text.
        Identify types such as PERSON, ORGANIZATION, LOCATION, DATE, EVENT, etc.
        Return a JSON object with a key "entities" which is a list of objects.
        Each object should have: "text", "type", "confidence" (0-1).

        Text: {text}
        """

        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts named entities. Output valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={ "type": "json_object" }
            )
            content = response.choices[0].message.content
            if content:
                result = json.loads(content)
                return result.get("entities", [])
            return []
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            # Fallback to empty list or heuristic on error?
            # For now return empty list to avoid duplicate logic or partial results
            return []
    
    async def summarize(self, text: str, max_length: int = 100) -> str:
        """
        Summarize text to specified length
        
        Args:
            text: Text to summarize
            max_length: Maximum length of summary
            
        Returns:
            Summarized text
        """
        # Placeholder for actual summarization
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."
    
    async def classify_topic(self, text: str) -> Dict[str, float]:
        """
        Classify text into topic categories
        
        Returns:
            Dict of topics with confidence scores
        """
        if not self.client:
            # Fallback for when API is not available
            return {
                "general": 0.7,
                "politics": 0.2,
                "technology": 0.1
            }

        prompt = f"""
        Classify the following text into relevant topics (e.g., politics, technology, economy, entertainment, sports, science).
        Return a JSON object where keys are topics and values are confidence scores between 0 and 1.

        Text: {text}
        """

        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that classifies text into topics. Output valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={ "type": "json_object" }
            )
            content = response.choices[0].message.content
            if content:
                return json.loads(content)
            else:
                return {"error": 1.0}
        except Exception as e:
            logger.error(f"Error classifying topic: {e}")
            return {
                "general": 0.7,
                "politics": 0.2,
                "technology": 0.1
            }
    
    async def extract_keywords(self, text: str, top_k: int = 5) -> List[str]:
        """
        Extract key terms from text
        
        Args:
            text: Input text
            top_k: Number of keywords to extract
            
        Returns:
            List of keywords
        """
        # Placeholder for keyword extraction
        words = text.lower().split()
        return list(set(words[:top_k]))
