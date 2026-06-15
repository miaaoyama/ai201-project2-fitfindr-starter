"""
agent.py

FitFindr planning loop.
"""

import re

from tools import search_listings, suggest_outfit, create_fit_card, compare_price


def _new_session(query: str, wardrobe: dict) -> dict:
    return {
        "query": query,
        "parsed": {},
        "search_results": [],
        "selected_item": None,
        "wardrobe": wardrobe,
        "price_assessment": None,
        "outfit_suggestion": None,
        "fit_card": None,
        "error": None,
        "fallback_message": None,
    }


def run_agent(query: str, wardrobe: dict) -> dict:
    session = _new_session(query, wardrobe)

    price_match = re.search(r"\$?(\d+(?:\.\d+)?)", query)
    max_price = float(price_match.group(1)) if price_match else None

    size_match = re.search(r"size\s+([A-Za-z0-9/]+)", query, re.IGNORECASE)
    size = size_match.group(1).upper() if size_match else None

    description = query.lower()
    description = re.sub(r"under\s+\$?\d+(?:\.\d+)?", "", description)
    description = re.sub(r"\$?\d+(?:\.\d+)?", "", description)
    description = re.sub(r"size\s+[A-Za-z0-9/]+", "", description)
    description = description.replace("looking for", "")
    description = description.replace("i'm", "")
    description = description.replace("im", "")
    description = description.strip(" .,")

    session["parsed"] = {
        "description": description,
        "size": size,
        "max_price": max_price,
    }

    results = search_listings(description, size=size, max_price=max_price)

    if not results:
        fallback_results = search_listings(description, size=None, max_price=None)

        if fallback_results:
            results = fallback_results
            session["fallback_message"] = (
                "No exact matches found. FitFindr retried without the size and price filters."
            )
        else:
            session["error"] = (
                f"No listings found for '{description}'"
                + (f" in size {size}" if size else "")
                + (f" under ${max_price:.0f}" if max_price else "")
                + ". Try a broader description, higher budget, or removing the size filter."
            )
            return session

    session["search_results"] = results
    session["selected_item"] = results[0]

    session["price_assessment"] = compare_price(session["selected_item"])

    outfit = suggest_outfit(session["selected_item"], session["wardrobe"])
    session["outfit_suggestion"] = outfit

    if not outfit:
        session["error"] = "Could not create an outfit suggestion."
        return session

    fit_card = create_fit_card(session["outfit_suggestion"], session["selected_item"])
    session["fit_card"] = fit_card

    return session


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )

    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        if session.get("fallback_message"):
            print(f"Fallback: {session['fallback_message']}")
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nPrice Assessment: {session['price_assessment']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== Fallback path ===\n")
    session2 = run_agent(
        query="graphic tee size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )

    if session2["error"]:
        print(f"Error message: {session2['error']}")
    else:
        print(f"Fallback: {session2.get('fallback_message')}")
        print(f"Found: {session2['selected_item']['title']}")
        print(f"\nPrice Assessment: {session2['price_assessment']}")
        print(f"Fit card: {session2['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session3 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session3['error']}")