# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
This tool searches the secondhand listings dataset for items matching the user's requested description, size, and budget. It filters listings and returns the best matching items sorted by relevance.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): string describing what the user wants, such as "vintage graphic tee" or "black leather jacket".
- `size` (str): string clothing size, such as "S", "M", "L", or None if the user did not specify size.
- `max_price` (float): float maximum price, such as 30.0, or None if the user did not specify a budget.

**What it returns:**
<!-- Describe the return value — what fields does a result contain? -->
Returns a dictionary containing:
- success (bool): whether any listings were found
- results (list): matching listing dictionaries
- message (str): explanation of the result

Each listing dictionary contains:
id, title, description, category, style_tags, size, condition, price, colors, brand, and platform.

**What happens if it fails or returns nothing:**
<!-- What should the agent do if no listings match? -->
If no listings match, the tool returns success=False, results=[], and a message such as: "No listings found for vintage graphic tee in size M under $30. Try a higher budget, broader description, or removing the size filter." The agent should not call suggest_outfit if this tool returns no results.

---

### Tool 2: suggest_outfit

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
This tool takes the selected thrift listing and the user’s wardrobe, then creates one or more outfit combinations using the new item and existing wardrobe pieces.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): dictionary for the selected listing from search_listings.
- `wardrobe` (list[dict])): list of wardrobe item dictionaries from get_example_wardrobe() or get_empty_wardrobe().

**What it returns:**
<!-- Describe the return value -->
Each outfit suggestion dictionary contains:
- new_item
- wardrobe_items
- styling_notes
- vibe


**What happens if it fails or returns nothing:**
<!-- What should the agent do if the wardrobe is empty or no outfit can be suggested? -->
If new_item is missing or empty, return success=False and a message explaining that no thrift item was selected. If the wardrobe is empty or too minimal, return a fallback outfit suggestion using only general basics, such as jeans, sneakers, or a neutral jacket, and explain that the suggestion is less personalized because the wardrobe data is empty.

---

### Tool 3: create_fit_card

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
This tool turns the outfit suggestion into a short, shareable caption that sounds like something someone might post with an outfit photo.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (dict): one outfit suggestion dictionary from suggest_outfit.
- `new_item` (dict): the selected listing dictionary from search_listings.

**What it returns:**
<!-- Describe the return value -->
- 'success' : boolean
- 'fit_card' : string caption
- 'message' : string explaining the result

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the outfit data is incomplete? -->
If the outfit or new item is missing, return success=False and a message such as: "I need both a selected item and an outfit suggestion before I can create a fit card." The agent should show the user this message instead of generating a fake caption.
---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->
1. Receive the user query.

2. Extract:
- description
- size
- max_price

3. Call search_listings(description, size, max_price).

4. If search_listings returns no results:
   - Save the error message.
   - Return a helpful response to the user.
   - Stop the workflow.

5. If results are found:
   - Save all results.
   - Select the first result as selected_item.

6. Load the user's wardrobe.

7. Call suggest_outfit(selected_item, wardrobe).

8. If suggest_outfit fails:
   - Save the error message.
   - Return the message to the user.
   - Stop the workflow.

9. If an outfit is returned:
   - Save the outfit suggestion.

10. Call create_fit_card(outfit_suggestion, selected_item).

11. If create_fit_card succeeds:
   - Save the fit card.
   - Return the item, outfit suggestion, and fit card to the user.

12. End workflow.

---

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->
The agent stores information in a session dictionary throughout the interaction.

Tracked state:
- user_query
- description
- size
- max_price
- search_results
- selected_item
- wardrobe
- outfit_suggestion
- fit_card
- error_message

The result of search_listings becomes selected_item. The selected_item is passed to suggest_outfit along with the wardrobe. The resulting outfit_suggestion is passed to create_fit_card. This allows information to flow between tools without asking the user to repeat information.

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | Tell the user no matching items were found and suggest increasing budget, removing size restrictions, or broadening the description. Stop workflow.|
| suggest_outfit | Wardrobe is empty | Generate a basic outfit using common wardrobe staples and explain that the recommendation is less personalized.|
| create_fit_card | Outfit input is missing or incomplete | Inform the user that a valid outfit and item are required before generating a fit card. Stop workflow.|

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     ASCII art, a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html), or an embedded
     sketch are all fine. You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->
User Query
    │
    ▼
Planning Loop
    │
    ▼
search_listings(description, size, max_price)
    │
    ├── No Results
    │       │
    │       ▼
    │   Error Message
    │       │
    │       ▼
    │     Return
    │
    ▼
Session:
selected_item = results[0]
    │
    ▼
suggest_outfit(selected_item, wardrobe)
    │
    ▼
Session:
outfit_suggestion
    │
    ▼
create_fit_card(outfit_suggestion, selected_item)
    │
    ▼
Session:
fit_card
    │
    ▼
Return Final Response

---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**
I will use Claude to implement each tool individually. 
For search_listings, I will provide the Tool 1 specification and ask for a function that uses load_listings() from the provided data loader. 
I will verify that it filters by description, size, and max_price and correctly handles empty results.

For suggest_outfit, I will provide the Tool 2 specification and wardrobe schema. I will verify that it produces outfit suggestions for both example wardrobes and empty wardrobes.

For create_fit_card, I will provide the Tool 3 specification and example captions. I will verify that the generated captions change based on the selected item and outfit.

**Milestone 4 — Planning loop and state management:**
I will provide Claude with the Planning Loop, State Management section, and Architecture diagram. 
I will ask it to implement the agent loop and session state. 
Before using the code, I will verify that the workflow stops when search_listings fails and that data is correctly passed between tools through session state.
---

## A Complete Interaction (Step by Step)

FitFindr helps the user search for a secondhand clothing item, choose a useful listing, style it with their existing wardrobe, and turn the final outfit into a shareable fit card. The search_listings tool runs first when the user describes what they want, and if it finds a good item, that item is passed into suggest_outfit along with the user's wardrobe. If search fails or returns no matches, the agent should explain what happened and stop or retry with looser filters instead of calling the outfit or fit card tools with empty data.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
<!-- What does the agent do first? Which tool is called? With what input? -->
The planning loop extracts:
description = "vintage graphic tee"
size = None
max_price = 30.0

The agent calls:
search_listings("vintage graphic tee", None, 30.0)

**Step 2:**
<!-- What happens next? What was returned from step 1? What tool is called now? -->
search_listings returns matching listings.

The agent stores:
selected_item = results[0]

The wardrobe is loaded using get_example_wardrobe().

The agent calls:
suggest_outfit(selected_item, wardrobe)

**Step 3:**
<!-- Continue until the full interaction is complete -->
suggest_outfit returns an outfit recommendation.

The agent stores:
outfit_suggestion

The agent calls:
create_fit_card(outfit_suggestion, selected_item)
create_fit_card returns a social-media-style caption.

The agent stores:
fit_card

**Final output to user:**
<!-- What does the user actually see at the end? -->
Final output to user:
Found: Faded Band Tee — $22 on Depop

Outfit suggestion:
Pair it with baggy jeans and chunky sneakers for a relaxed 90s-inspired streetwear look.

Fit card:
"thrifted this faded band tee off depop for $22 and honestly it was made for my wide-legs 🖤"
