# FitFindr

FitFindr is a multi-tool AI agent that helps users search for secondhand clothing items, style them with an existing wardrobe, and generate a short shareable outfit caption. The agent uses a planning loop instead of calling every tool blindly, so it changes behavior depending on whether the search succeeds or fails.

## Tools

### `search_listings(description: str, size: str | None, max_price: float | None) -> list[dict]`

Purpose: Searches the mock thrift listings dataset for items that match the user’s requested description, optional size, and optional price limit.

Inputs:

* `description`: keywords for the item the user wants.
* `size`: optional clothing size filter.
* `max_price`: optional maximum price.

Output:

* A list of listing dictionaries sorted by relevance.
* Each listing includes fields such as `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Failure behavior:

* If no listings match, the tool returns `[]` instead of raising an exception.

### `suggest_outfit(new_item: dict, wardrobe: dict) -> str`

Purpose: Takes the selected thrift item and the user’s wardrobe, then asks the LLM to suggest one or two outfit combinations.

Inputs:

* `new_item`: the selected listing dictionary from `search_listings`.
* `wardrobe`: a wardrobe dictionary with an `items` list.

Output:

* A non-empty string with outfit suggestions.

Failure behavior:

* If the wardrobe is empty, the tool still returns general styling advice instead of crashing.

### `create_fit_card(outfit: str, new_item: dict) -> str`

Purpose: Turns the outfit suggestion into a short caption for a social media-style fit card.

Inputs:

* `outfit`: the outfit suggestion string from `suggest_outfit`.
* `new_item`: the selected thrift listing.

Output:

* A short caption mentioning the item, price, platform, and outfit vibe.

Failure behavior:

* If the outfit string is empty, the tool returns a descriptive error message instead of calling the LLM with incomplete input.

## Planning Loop

The agent starts by creating a session dictionary that stores the query, parsed parameters, search results, selected item, wardrobe, outfit suggestion, fit card, and any error.

The planning loop follows these steps:

1. Parse the user query for item description, size, and max price.
2. Call `search_listings(description, size, max_price)`.
3. If search returns an empty list, save an error message in `session["error"]` and return early.
4. If results are found, save them in `session["search_results"]`.
5. Select the top result and save it in `session["selected_item"]`.
6. Call `suggest_outfit(session["selected_item"], session["wardrobe"])`.
7. Save the result in `session["outfit_suggestion"]`.
8. Call `create_fit_card(session["outfit_suggestion"], session["selected_item"])`.
9. Save the result in `session["fit_card"]`.
10. Return the full session.

The important branch is after search. If `search_listings` returns no results, the agent does not call `suggest_outfit` or `create_fit_card`.

## State Management

State is passed through a session dictionary. This prevents the user from having to repeat information between steps.

Important session fields:

* `query`
* `parsed`
* `search_results`
* `selected_item`
* `wardrobe`
* `outfit_suggestion`
* `fit_card`
* `error`

The selected listing from `search_listings` becomes `session["selected_item"]`. That same dictionary is passed into `suggest_outfit`. The outfit string returned by `suggest_outfit` becomes `session["outfit_suggestion"]`, which is then passed into `create_fit_card`.

## Error Handling

### No search results

Test command:

```bash
python -c "from tools import search_listings; print(search_listings('designer ballgown', size='XXS', max_price=5))"
```

Result:

```text
[]
```

Full agent behavior:
The agent returns a helpful message such as:

```text
No listings found for 'designer ballgown' in size XXS under $5. Try a broader description, higher budget, or removing the size filter.
```

The agent stops early and does not create an outfit or fit card.

### Empty wardrobe

Test command:

```bash
python -c "from tools import search_listings, suggest_outfit; from utils.data_loader import get_empty_wardrobe; results = search_listings('vintage graphic tee', size=None, max_price=50); print(suggest_outfit(results[0], get_empty_wardrobe()))"
```

Behavior:
The tool returns general styling advice instead of crashing.

### Empty outfit input

Test command:

```bash
python -c "from tools import search_listings, create_fit_card; results = search_listings('vintage graphic tee', size=None, max_price=50); print(create_fit_card('', results[0]))"
```

Behavior:
The tool returns:

```text
I need an outfit suggestion before I can create a fit card.
```

## Testing

I tested the tools with pytest:

```bash
python -m pytest tests/
```

Current result:

```text
5 passed
```

The tests cover:

* search returns results
* search returns an empty list for impossible queries
* price filtering
* empty wardrobe handling
* empty outfit handling

## AI Usage

I used Claude to help turn my planning.md specifications into implementation steps. For the tools, I gave Claude the Tool 1, Tool 2, and Tool 3 sections from planning.md, including each function’s inputs, outputs, and failure behavior. It produced draft implementations, and I revised them to match the starter repo’s expected return types, especially making sure `search_listings` returned a list rather than a dictionary.

I also used Claude for debugging pytest and Git issues. For example, when pytest could not import `tools.py`, I switched to running tests with `python -m pytest tests/`. When `search_listings` returned an empty list for every query, I removed the broad `try/except` that was hiding the real issue and updated the search logic.

## Spec Reflection

The most important design choice was making the agent stop early when search fails. Without that branch, the agent would try to style an item that does not exist, which would make the workflow feel fake and unreliable.

Testing each tool in isolation made the planning loop easier to debug. Once I knew that `search_listings`, `suggest_outfit`, and `create_fit_card` worked independently, I could focus on whether state was being passed correctly between them.

One thing I would improve in a future version is the query parser. Right now it uses simple regex and string cleanup. A more robust version could use an LLM or a structured parser to better separate item description, size, budget, and wardrobe preferences.

## Stretch Feature: Retry Logic with Fallback

If the first search returns no results, FitFindr automatically retries the search without the size and price filters. The agent stores a `fallback_message` in the session explaining what was adjusted.

Example:
`baby tee size XXS under $5`

The exact search fails because there is no baby tee in size XXS under $5. FitFindr then retries using only the item description, finds a baby tee, and continues through outfit suggestion and fit card generation.
