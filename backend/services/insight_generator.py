"""AI insight generation service.

Calls Groq API (llama-3.3-70b-versatile) to convert computed analytics
statistics into a single, specific, numbers-citing sentence for display
alongside charts.

Rate limit handling is delegated to _call_with_retry from llm_structurer,
which applies exponential backoff (5s → 10s → 20s) on HTTP 429 errors and
raises GroqAPIError after 3 failed attempts.
"""

try:
    from services.llm_structurer import GroqAPIError, _call_with_retry, _get_client
except ImportError:
    from backend.services.llm_structurer import GroqAPIError, _call_with_retry, _get_client

_MODEL = "llama-3.3-70b-versatile"

_INSIGHT_SYSTEM_PROMPT = (
    "You are a concise financial analyst. "
    "All monetary amounts are in Nepali Rupees (NPR). "
    "Always use 'NPR' as the currency symbol, never '$' or 'USD'. "
    "Given spending statistics, write exactly one sentence that describes the pattern. "
    "Be specific: cite the exact numbers provided with NPR currency. "
    "Never use the words 'should', 'consider', or 'recommend'. "
    "Never give financial advice. "
    "Output only the sentence, no preamble or trailing punctuation beyond the period."
)


def generate_insight(pattern_type: str, computed_data: dict) -> str:
    """Generate a one-sentence AI insight for a spending pattern.

    Calls Groq API (llama-3.3-70b-versatile) with the computed analytics
    data and the pattern type as context, then returns the model's
    single-sentence response.

    Args:
        pattern_type: Human-readable pattern label, e.g. ``"day-of-week"``,
            ``"monthly-trend"``, ``"category-breakdown"``, ``"anomalies"``.
        computed_data: The analytics dict returned by the corresponding
            pattern_analytics function.

    Returns:
        A single sentence (str) describing the pattern with specific numbers.

    Raises:
        GroqAPIError: If the Groq API key is missing, the rate limit is
            exhausted after 3 retries, or any other unrecoverable API error
            occurs.
    """
    client = _get_client()

    user_prompt = (
        f"Based on these statistics: {computed_data}, "
        f"write one sentence describing the {pattern_type} pattern. "
        "Be specific and cite numbers with NPR currency symbol. "
        "Do not use words like 'should', 'consider', or 'recommend'."
    )

    def _api_call():
        response = client.chat.completions.create(
            model=_MODEL,
            messages=[
                {"role": "system", "content": _INSIGHT_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=128,
        )
        return response

    try:
        response = _call_with_retry(_api_call)
    except GroqAPIError:
        raise
    except Exception as exc:
        raise GroqAPIError(f"Groq API call failed in insight_generator: {exc}") from exc

    # Handle case when response is None (all API keys exhausted)
    if response is None or not hasattr(response, 'choices') or not response.choices:
        raise GroqAPIError(
            "Rate limit reached on all API keys. Please try again in a few minutes."
        )

    insight = response.choices[0].message.content.strip()
    return insight
