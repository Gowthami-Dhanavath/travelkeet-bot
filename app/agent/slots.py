import re


class SlotExtractor:
    def __init__(self):
        with open("prompts/slot_extraction.md", "r", encoding="utf-8") as f:
            self.prompt = f.read()

    async def extract(self, message: str, current_slots: dict):
        text = message.lower()
        updated_slots = dict(current_slots or {})

        route = re.search(
            r"\bfrom\s+([a-z][a-z\s]+?)\s+(?:to|towards)\s+([a-z][a-z\s]+?)(?:[,.!?]|\s+for\b|\s+with\b|\s+on\b|$)",
            text,
        )
        if route:
            updated_slots["from_city"] = route.group(1).strip().title()
            updated_slots["to_city"] = route.group(2).strip().title()

        to_city = re.search(
            r"\b(?:to|towards)\s+([a-z][a-z\s]+?)(?:[,.!?]|\s+from\b|\s+for\b|\s+with\b|\s+on\b|$)",
            text,
        )
        if to_city and "to_city" not in updated_slots:
            updated_slots["to_city"] = to_city.group(1).strip().title()

        adults = re.search(r"\b(\d+)\s*(?:adults?|people|travellers?|travelers?|pax)\b", text)
        if adults:
            updated_slots["num_adults"] = int(adults.group(1))

        budget = re.search(r"(?:budget|under|below|upto|up to)\s*(?:inr|rs\.?|₹)?\s*([\d,]+)", text)
        if budget:
            updated_slots["budget_inr"] = int(budget.group(1).replace(",", ""))

        return updated_slots

