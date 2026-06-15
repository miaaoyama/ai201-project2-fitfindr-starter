"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    listings = load_listings()
    query_words = set(description.lower().split())

    matches = []

    for item in listings:
        price = float(item.get("price", 0))

        if max_price is not None and price > max_price:
            continue

        if size is not None:
            item_size = str(item.get("size", "")).lower()
            if size.lower() not in item_size:
                continue

        searchable_text = " ".join([
            str(item.get("title", "")),
            str(item.get("description", "")),
            str(item.get("category", "")),
            " ".join(item.get("style_tags", [])),
            " ".join(item.get("colors", [])),
            str(item.get("brand", "")),
            str(item.get("platform", "")),
        ]).lower()

        score = sum(1 for word in query_words if word in searchable_text)

        if score > 0:
            matches.append((score, item))

    matches.sort(key=lambda pair: pair[0], reverse=True)

    return [item for score, item in matches]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    try:
        client = _get_groq_client()

        wardrobe_items = wardrobe.get("items", []) if wardrobe else []

        item_details = f"""
Item:
Title: {new_item.get("title", "Unknown item")}
Description: {new_item.get("description", "")}
Category: {new_item.get("category", "")}
Style tags: {new_item.get("style_tags", [])}
Colors: {new_item.get("colors", [])}
Price: {new_item.get("price", "")}
Platform: {new_item.get("platform", "")}
"""

        if not wardrobe_items:
            prompt = f"""
You are FitFindr, a helpful thrift styling assistant.

The user is considering this thrifted item:
{item_details}

The user's wardrobe is empty or unavailable.

Suggest 1-2 complete outfit ideas using common wardrobe basics.
Be specific, stylish, and helpful. Mention that the advice is less personalized because no wardrobe items were provided.
"""
        else:
            wardrobe_text = "\n".join(
                [
                    f"- {item.get('name', item.get('title', 'Unnamed item'))}: "
                    f"{item.get('category', '')}, {item.get('colors', [])}, "
                    f"{item.get('style_tags', [])}"
                    for item in wardrobe_items
                ]
            )

            prompt = f"""
You are FitFindr, a helpful thrift styling assistant.

The user is considering this thrifted item:
{item_details}

The user's wardrobe includes:
{wardrobe_text}

Suggest 1-2 complete outfits using the thrifted item and specific pieces from the wardrobe.
Make the styling advice practical, visual, and fashion-aware.
"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a stylish secondhand fashion assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"Sorry, I couldn't create an outfit suggestion right now: {e}"


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    try:
        if not outfit or not outfit.strip():
            return "I need an outfit suggestion before I can create a fit card."

        client = _get_groq_client()

        prompt = f"""
Create a short, shareable outfit caption for this thrifted find.

New item:
Title: {new_item.get("title", "Unknown item")}
Price: ${new_item.get("price", "")}
Platform: {new_item.get("platform", "")}
Description: {new_item.get("description", "")}

Outfit suggestion:
{outfit}

Requirements:
- 2 to 4 sentences
- Casual and authentic, like an OOTD post
- Mention the item name, price, and platform naturally once
- Do not sound like a product description
- Make it stylish and social-media friendly
"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You write stylish, casual outfit captions."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.9,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"Sorry, I couldn't create a fit card right now: {e}"
