#!/usr/bin/env python
"""
Text Analysis Agent for A2A Network

This agent performs text analysis tasks including general analysis,
summarization, and sentiment analysis.
"""

import logging
import os
import re
import string
import sys
from typing import Any, Dict

# Add parent directory to PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from libs.pepperpya2a.src.pepperpya2a import create_a2a_server

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TextAgent:
    """
    Text Analysis Agent for A2A Network.

    This agent provides capabilities for:
    - General text analysis (length, structure, key points)
    - Text summarization (with configurable length)
    - Sentiment analysis (positive/negative assessment)
    """

    def __init__(self, port: int = 8082):
        """
        Initialize the text analysis agent.

        Args:
            port: Port to run the agent on
        """
        self.server = create_a2a_server(
            name="Text Analysis Agent",
            description="Analyzes text content for insights, summaries, and sentiment",
            system_prompt="You are a text analysis agent that specializes in understanding and processing text",
            port=port,
        )

        # Load sentiment lexicons
        self.positive_words = set(
            [
                "good",
                "great",
                "excellent",
                "amazing",
                "wonderful",
                "fantastic",
                "terrific",
                "outstanding",
                "superb",
                "brilliant",
                "positive",
                "nice",
                "happy",
                "joy",
                "love",
                "beautiful",
                "perfect",
                "awesome",
                "delightful",
                "pleasant",
                "favorable",
                "impressive",
                "remarkable",
                "exceptional",
            ]
        )

        self.negative_words = set(
            [
                "bad",
                "terrible",
                "awful",
                "horrible",
                "poor",
                "negative",
                "sad",
                "disappointing",
                "unfortunate",
                "unpleasant",
                "mediocre",
                "inferior",
                "inadequate",
                "unfavorable",
                "dreadful",
                "appalling",
                "atrocious",
                "subpar",
                "dismal",
                "grim",
                "depressing",
                "miserable",
                "tragic",
            ]
        )

        # Register capabilities
        self.server.register_capability(
            name="analyze_text",
            description="Analyze a text passage for key information, structure, and content",
            input_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "The text to analyze"},
                    "include_metrics": {
                        "type": "boolean",
                        "description": "Whether to include detailed metrics",
                        "default": True,
                    },
                },
                "required": ["text"],
            },
            handler=self.analyze_text,
        )

        self.server.register_capability(
            name="summarize",
            description="Generate a concise summary of a longer text",
            input_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "The text to summarize"},
                    "length": {
                        "type": "string",
                        "description": "Desired summary length",
                        "enum": ["short", "medium", "long"],
                        "default": "medium",
                    },
                },
                "required": ["text"],
            },
            handler=self.summarize,
        )

        self.server.register_capability(
            name="analyze_sentiment",
            description="Determine the sentiment (positive, negative, neutral) of a text",
            input_schema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text for sentiment analysis",
                    },
                    "detailed": {
                        "type": "boolean",
                        "description": "Whether to include detailed analysis breakdown",
                        "default": False,
                    },
                },
                "required": ["text"],
            },
            handler=self.analyze_sentiment,
        )

    async def start(self):
        """Start the text analysis agent server."""
        await self.server.start_server()
        logger.info("Text analysis agent started successfully")

    async def close(self):
        """Close the agent server."""
        await self.server.close()
        logger.info("Text analysis agent stopped")

    async def analyze_text(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a text passage for key information, structure, and content.

        Args:
            data: Input data containing the text to analyze

        Returns:
            Analysis results including word count, sentence count, and key points
        """
        try:
            text = data.get("text", "")
            include_metrics = data.get("include_metrics", True)

            if not text:
                logger.error("No text provided for analysis")
                return {"error": "No text provided for analysis"}

            logger.info(f"Analyzing text of length {len(text)}")

            # Basic metrics
            words = text.split()
            word_count = len(words)
            sentences = re.split(r"[.!?]+", text)
            sentences = [s.strip() for s in sentences if s.strip()]
            sentence_count = len(sentences)

            # Calculate average sentence length
            avg_words_per_sentence = word_count / max(1, sentence_count)

            # Identify paragraphs
            paragraphs = text.split("\n\n")
            paragraphs = [p.strip() for p in paragraphs if p.strip()]
            paragraph_count = len(paragraphs)

            # Extract important words (simple implementation)
            important_words = self._extract_important_words(text)

            # Language characteristics
            language_assessment = self._assess_language(text)

            # Identify potential key points (simple heuristic - sentences with important words)
            key_points = []
            for sentence in sentences:
                words_in_sentence = set(re.findall(r"\b\w+\b", sentence.lower()))
                importance_score = len(words_in_sentence.intersection(important_words))
                if importance_score >= 2:  # Threshold for considering a key point
                    key_points.append(sentence)

            # Limit key points to 5
            key_points = key_points[:5]

            result = {
                "word_count": word_count,
                "sentence_count": sentence_count,
                "paragraph_count": paragraph_count,
                "avg_words_per_sentence": round(avg_words_per_sentence, 1),
                "key_points": key_points,
                "language_characteristics": language_assessment,
                "important_words": list(important_words)[:15],  # Top 15 important words
            }

            # Add detailed metrics if requested
            if include_metrics:
                result["metrics"] = {
                    "unique_words": len(set(w.lower() for w in words)),
                    "longest_sentence_words": max(len(s.split()) for s in sentences),
                    "shortest_sentence_words": min(
                        len(s.split()) for s in sentences if s
                    ),
                    "avg_paragraph_sentences": round(
                        sentence_count / max(1, paragraph_count), 1
                    ),
                }

            logger.info(
                f"Completed text analysis with {word_count} words and {sentence_count} sentences"
            )
            return result

        except Exception as e:
            error_msg = f"Error analyzing text: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"error": error_msg}

    async def summarize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a concise summary of a longer text.

        Args:
            data: Input data containing the text to summarize and desired length

        Returns:
            A summary of the requested length
        """
        try:
            text = data.get("text", "")
            length = data.get("length", "medium").lower()

            if not text:
                logger.error("No text provided for summarization")
                return {"error": "No text provided for summarization"}

            logger.info(f"Summarizing text of length {len(text)} with {length} summary")

            # Break text into sentences
            sentences = re.split(r"[.!?]+", text)
            sentences = [s.strip() for s in sentences if s.strip()]

            if not sentences:
                return {"error": "Could not extract meaningful sentences from text"}

            # Calculate importance score for each sentence
            important_words = self._extract_important_words(text)
            sentence_scores = []

            for i, sentence in enumerate(sentences):
                words_in_sentence = set(re.findall(r"\b\w+\b", sentence.lower()))

                # Score based on important words presence
                importance_score = len(words_in_sentence.intersection(important_words))

                # Bonus for sentences at the beginning or end
                position_score = 0
                if i < len(sentences) * 0.2:  # First 20% of sentences
                    position_score += 2
                elif i > len(sentences) * 0.8:  # Last 20% of sentences
                    position_score += 1

                # Penalty for very short sentences
                length_score = min(len(words_in_sentence) / 5, 2)

                total_score = importance_score + position_score + length_score
                sentence_scores.append((sentence, total_score))

            # Sort sentences by score
            sentence_scores.sort(key=lambda x: x[1], reverse=True)

            # Determine number of sentences to include based on requested length
            if length == "short":
                num_sentences = min(3, len(sentences))
            elif length == "medium":
                num_sentences = min(5, len(sentences))
            else:  # long
                num_sentences = min(7, len(sentences))

            # Get top scoring sentences
            top_sentences = [s[0] for s in sentence_scores[:num_sentences]]

            # Re-order sentences to maintain the original flow
            original_order = []
            for sentence in sentences:
                if sentence in top_sentences:
                    original_order.append(sentence)

            # Create summary
            summary = ". ".join(original_order)
            if not summary.endswith((".", "!", "?")):
                summary += "."

            # Create a summary title (simple implementation)
            important_phrases = list(important_words)[:3]
            title = " ".join(w.capitalize() for w in important_phrases)

            logger.info(
                f"Created {length} summary with {len(original_order)} sentences"
            )

            return {
                "summary": summary,
                "title": title,
                "length": length,
                "sentence_count": len(original_order),
                "original_sentence_count": len(sentences),
                "reduction_percentage": round(
                    (1 - len(original_order) / len(sentences)) * 100, 1
                ),
            }

        except Exception as e:
            error_msg = f"Error summarizing text: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"error": error_msg}

    async def analyze_sentiment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine the sentiment (positive, negative, neutral) of a text.

        Args:
            data: Input data containing the text for sentiment analysis

        Returns:
            Sentiment analysis results with score and assessment
        """
        try:
            text = data.get("text", "")
            detailed = data.get("detailed", False)

            if not text:
                logger.error("No text provided for sentiment analysis")
                return {"error": "No text provided for sentiment analysis"}

            logger.info(f"Analyzing sentiment of text with length {len(text)}")

            # Convert to lowercase and tokenize
            text_lower = text.lower()

            # Remove punctuation and split into words
            translator = str.maketrans("", "", string.punctuation)
            text_no_punct = text_lower.translate(translator)
            words = text_no_punct.split()

            # Count positive and negative words
            positive_count = 0
            negative_count = 0

            # Check for negations
            negations = [
                "not",
                "no",
                "never",
                "cannot",
                "doesn't",
                "isn't",
                "aren't",
                "wasn't",
                "weren't",
                "don't",
            ]
            negation_detected = False

            positive_matches = []
            negative_matches = []

            for i, word in enumerate(words):
                # Check for negations (looking at previous word)
                if i > 0 and words[i - 1] in negations:
                    negation_detected = True
                else:
                    negation_detected = False

                # Check sentiment and handle negation
                if word in self.positive_words:
                    if negation_detected:
                        negative_count += 1
                        negative_matches.append(word)
                    else:
                        positive_count += 1
                        positive_matches.append(word)

                elif word in self.negative_words:
                    if negation_detected:
                        positive_count += 1
                        positive_matches.append(word)
                    else:
                        negative_count += 1
                        negative_matches.append(word)

            # Calculate sentiment score (from -1 to +1)
            total_sentiment_words = positive_count + negative_count
            if total_sentiment_words > 0:
                sentiment_score = (
                    positive_count - negative_count
                ) / total_sentiment_words
            else:
                sentiment_score = 0

            # Determine overall sentiment
            if sentiment_score > 0.1:
                sentiment = "positive"
                if sentiment_score > 0.5:
                    strength = "strongly"
                else:
                    strength = "moderately"
            elif sentiment_score < -0.1:
                sentiment = "negative"
                if sentiment_score < -0.5:
                    strength = "strongly"
                else:
                    strength = "moderately"
            else:
                sentiment = "neutral"
                strength = ""

            # Identify emotional tone
            emotional_tone = self._identify_emotional_tone(text_lower, sentiment)

            result = {
                "sentiment": sentiment,
                "score": round(sentiment_score, 2),
                "assessment": f"{strength} {sentiment}".strip(),
                "emotional_tone": emotional_tone,
            }

            # Add detailed breakdown if requested
            if detailed:
                result["details"] = {
                    "positive_word_count": positive_count,
                    "negative_word_count": negative_count,
                    "total_words": len(words),
                    "sentiment_words_percentage": round(
                        (total_sentiment_words / len(words)) * 100, 1
                    ),
                    "positive_words": positive_matches[:10],  # Top 10 matches
                    "negative_words": negative_matches[:10],  # Top 10 matches
                }

            logger.info(f"Completed sentiment analysis: {result['assessment']}")
            return result

        except Exception as e:
            error_msg = f"Error analyzing sentiment: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"error": error_msg}

    def _extract_important_words(self, text: str) -> set:
        """Extract important words from text, excluding stopwords."""
        # Simple stopwords list (would be more comprehensive in production)
        stopwords = set(
            [
                "the",
                "and",
                "a",
                "to",
                "of",
                "in",
                "that",
                "is",
                "it",
                "for",
                "with",
                "as",
                "on",
                "at",
                "by",
                "from",
                "an",
                "be",
                "or",
                "this",
                "but",
                "not",
                "are",
                "was",
                "were",
                "they",
                "their",
                "has",
                "have",
                "had",
                "can",
                "will",
                "would",
                "should",
                "could",
                "may",
                "might",
            ]
        )

        # Extract all words
        words = re.findall(r"\b[a-z]{3,}\b", text.lower())

        # Remove stopwords and count frequencies
        word_freq = {}
        for word in words:
            if word not in stopwords:
                word_freq[word] = word_freq.get(word, 0) + 1

        # Return set of words that appear more than once (or all if few words)
        if len(word_freq) < 10:
            return set(word_freq.keys())
        else:
            return set(word for word, freq in word_freq.items() if freq > 1)

    def _assess_language(self, text: str) -> Dict[str, Any]:
        """Assess language characteristics of the text."""
        # Simple metrics for language assessment
        words = text.split()
        if not words:
            return {"complexity": "unknown", "formality": "unknown"}

        # Average word length as proxy for complexity
        avg_word_length = sum(len(word) for word in words) / len(words)

        # Detect formal language markers
        formal_markers = [
            "therefore",
            "thus",
            "consequently",
            "furthermore",
            "moreover",
            "additionally",
            "subsequently",
            "nevertheless",
            "however",
            "accordingly",
            "regarding",
            "concerning",
            "hereby",
        ]

        formal_count = sum(1 for word in words if word.lower() in formal_markers)
        formal_ratio = formal_count / len(words)

        # Assess complexity
        if avg_word_length > 6:
            complexity = "high"
        elif avg_word_length > 4.5:
            complexity = "medium"
        else:
            complexity = "low"

        # Assess formality
        if formal_ratio > 0.02:
            formality = "formal"
        elif formal_ratio > 0.005:
            formality = "neutral"
        else:
            formality = "informal"

        return {
            "complexity": complexity,
            "formality": formality,
            "avg_word_length": round(avg_word_length, 1),
        }

    def _identify_emotional_tone(self, text: str, sentiment: str) -> str:
        """Identify the emotional tone of the text."""
        emotion_markers = {
            "joyful": ["happy", "joy", "delight", "thrilled", "excited", "wonderful"],
            "angry": ["angry", "furious", "outraged", "annoyed", "irritated"],
            "sad": ["sad", "depressed", "unhappy", "miserable", "gloomy"],
            "fearful": ["afraid", "scared", "frightened", "terrified", "worried"],
            "surprised": ["surprised", "amazed", "astonished", "shocked"],
            "analytical": ["analyze", "consider", "examine", "study", "evaluate"],
            "confident": ["confident", "certain", "sure", "definite", "absolute"],
            "tentative": ["perhaps", "maybe", "possibly", "might", "could"],
        }

        # Count emotion markers
        emotion_counts = {emotion: 0 for emotion in emotion_markers}

        for emotion, markers in emotion_markers.items():
            for marker in markers:
                emotion_counts[emotion] += text.count(marker)

        # Find dominant emotion
        max_emotion = max(emotion_counts.items(), key=lambda x: x[1])

        # If no strong emotions detected, base on sentiment
        if max_emotion[1] == 0:
            if sentiment == "positive":
                return "positive"
            elif sentiment == "negative":
                return "negative"
            else:
                return "neutral"

        return max_emotion[0]


async def main():
    """Main function to run the text analysis agent."""
    import asyncio

    text_agent = TextAgent()

    try:
        await text_agent.start()

        # Keep the server running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Received keyboard interrupt. Shutting down...")
    finally:
        await text_agent.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
