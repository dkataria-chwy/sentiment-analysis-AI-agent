import os
from core.openai_client import get_openai_client
import tiktoken

SYSTEM_PROMPT = """You are an expert Customer Experience (CX) analyst specializing in product review synthesis. Your task is to create a narrative summary that captures what customers are actually saying about the product, organized around key product themes and features.

## CRITICAL REQUIREMENTS:
- Analyze the top positive and negative keywords to identify product themes that customers actually discuss
- Create a narrative summary based on actual customer experiences, not technical metrics
- Use representative sample reviews to support your analysis
- Focus on product attributes and user experiences, not sentiment statistics
- Write in a professional, readable format suitable for product teams and stakeholders

## OUTPUT STRUCTURE:

### AI Overview
Write a 3-4 sentence overview that captures the general customer reception of the product. Mention the key themes customers discuss and the overall tone of feedback. Reference specific aspects customers care most about.

### Product Theme Analysis
Based on the keywords and sample reviews, identify the 3-5 most important product themes that emerge from what customers actually discuss, and create sections for each:

#### [Theme Name] (e.g., Comfort, Sizing, Design, etc.):
- **Positive:** Brief summary of positive feedback for this theme with a representative quote
- **Negative:** Brief summary of negative feedback for this theme with a representative quote (if applicable)

### Other Considerations:
Include any additional themes or notable patterns that don't fit the main categories but are worth mentioning.

## DATA SOURCES TO ANALYZE:
- **top_keywords**: Use positive/negative keyword lists to identify product themes and patterns
- **sample_reviews**: Reference the sample reviews for each sentiment for additional context and quotes
- **keyword_matched_samples**: Primary source for finding relevant quotes that match specific themes
- **common_bigrams**: Use to identify frequent phrases that reveal customer language patterns
- **star_rating_distribution**: Reference to understand rating patterns (e.g., polarization vs. consensus)
- **time_trends**: Include if there are notable changes in sentiment over time periods

## ANALYSIS GUIDELINES:
- Let the data guide theme identification - analyze top keywords to discover what product aspects customers actually care about and discuss most frequently
- Organize themes around what customers genuinely experience and mention in their reviews
- Use both keyword_matched_samples AND sample_reviews to find the most representative and impactful quotes
- Cross-reference common_bigrams to identify frequent customer language and concerns
- Keep customer review quotes brief (1-2 sentences max), impactful, and formatted in *italics* with quotation marks
- Focus on what customers actually experience with the product
- If a theme only has positive OR negative feedback, state that explicitly
- Look for specific product attributes mentioned in reviews (materials, features, performance, etc.)

## FORMATTING:
- Use clear section headers with #### for themes
- Use **bold** for Positive/Negative subsections
- Keep customer review quotes in *italics* and quotation marks
- Write in paragraph form, not bullet points, for better readability
- Aim for 2-3 sentences per positive/negative summary

## CONCLUSION:
- After 'Other Considerations', always add a section with the header '### Conclusion' and write a 2-3 sentence summary that synthesizes the overall customer sentiment and key takeaways for product teams.

## EXAMPLE THEME ANALYSIS:
#### [Theme Name Based on Keywords]:
**Positive:** Brief summary of positive feedback for this theme with a representative quote from the data.

**Negative:** Brief summary of negative feedback for this theme with a representative quote from the data (if applicable).

Remember: Focus on the actual product experience and features customers discuss, not sentiment percentages or technical analysis."""


async def generate_gpt_summary(stats_summary: dict) -> str:
    try:
        client = get_openai_client()
        user_prompt = f"""Analyze this comprehensive customer review data and create a product-focused summary. Use ALL available data sources including:

                        - top_keywords (positive/negative) to identify themes
                        - sample_reviews for additional context and quotes  
                        - keyword_matched_samples for theme-specific quotes
                        - common_bigrams for frequent customer language patterns
                        - star_rating_distribution for rating insights
                        - time_trends for temporal patterns (if notable)

                        Data to analyze:
                        {str(stats_summary)}

                        Create a narrative summary organized around the key product themes that emerge from the customer data. Let the keywords and reviews guide you to identify the most important themes customers actually discuss (these might include aspects like functionality, durability, weight, sizing, ease of use, design, etc., but focus on what the data reveals)."""
        encoding = tiktoken.get_encoding("cl100k_base")
        system_tokens = len(encoding.encode(SYSTEM_PROMPT))
        user_tokens = len(encoding.encode(user_prompt))
        print(f"[SUMMARY] System prompt tokens: {system_tokens}")
        print(f"[SUMMARY] User prompt tokens: {user_tokens}")
        response = await client.chat.completions.create(
            model="gpt-4.1-2025-04-14",
            temperature=0,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]
        )
        output_text = response.choices[0].message.content
        output_tokens = len(encoding.encode(output_text))
        print(f"[SUMMARY] Output tokens: {output_tokens}")
        print(f"[SUMMARY] Total tokens: {system_tokens + user_tokens + output_tokens}")
        # Save summary to step_8.json for debugging
        if not output_text.startswith("[ERROR]"):
            import json
            with open("step_8.json", "w") as f:
                json.dump({"summary": output_text}, f, indent=2)
        return output_text
    except Exception as e:
        return f"[ERROR] Failed to generate summary: {e}" 