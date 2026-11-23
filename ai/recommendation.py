"""
ai/recommendation.py  -  Smart product recommendation (Artificial Intelligence).

HONEST NOTE: there is no real training dataset in this project, so we do NOT
pretend to have a trained neural network. Instead we use a transparent
"weighted scoring" algorithm (a simple rule-based AI / decision-support system).
Every score can be explained step by step, which makes it easy to present.

Steps:
  1. Keep only products whose lowest price is inside the customer's budget.
  2. Give every product four scores between 0 and 1:
        price score   -> cheaper is better
        quality score -> rating, corrected by the number of reviews
        specs score   -> RAM, storage, camera, battery compared with the best product
        seller score  -> seller reliability / 5
  3. Multiply each score by a weight that depends on the customer's priority.
  4. Total = weighted sum x 100.  The highest total is the "best product".
  5. Write a plain-English reason for every recommendation.
"""

# Weights for each priority (each row adds up to 1.0)
WEIGHTS = {
    "balanced":    {"price": 0.25, "quality": 0.30, "specs": 0.25, "seller": 0.20},
    "price":       {"price": 0.50, "quality": 0.20, "specs": 0.15, "seller": 0.15},
    "quality":     {"price": 0.10, "quality": 0.50, "specs": 0.15, "seller": 0.25},
    "performance": {"price": 0.10, "quality": 0.20, "specs": 0.55, "seller": 0.15},
    "seller":      {"price": 0.10, "quality": 0.25, "specs": 0.10, "seller": 0.55},
}

PRIORITY_LABELS = {
    "balanced": "Balanced",
    "price": "Lowest price",
    "quality": "Best ratings",
    "performance": "Best specifications",
    "seller": "Most reliable seller",
}

PLATFORMS = {"Amazon": "price_amazon", "Flipkart": "price_flipkart", "Meesho": "price_meesho"}


# ------------------------------------------------------------ helpers
def lowest_price(product):
    """Return (price, platform) of the cheapest platform for a product."""
    prices = [(product[col], name) for name, col in PLATFORMS.items() if product[col]]
    return min(prices) if prices else (None, None)


def adjusted_rating(rating, reviews, average_rating, min_reviews=500):
    """
    Rating analysis. A 4.8 rating from 3 reviews is less trustworthy than a 4.5
    from 3000 reviews, so we pull small-sample ratings towards the average.
    adjusted = (v / (v + m)) * R + (m / (v + m)) * C
        R = product rating, v = reviews, C = average rating, m = confidence constant
    """
    return (reviews / (reviews + min_reviews)) * rating + (min_reviews / (reviews + min_reviews)) * average_rating


def quality_label(adjusted, seller):
    """Product quality analysis: combine adjusted rating and seller reliability."""
    score = 0.7 * adjusted + 0.3 * seller
    if score >= 4.4:
        return "Excellent"
    if score >= 4.1:
        return "Good"
    if score >= 3.7:
        return "Average"
    return "Needs caution"


def scale(value, low, high):
    """Scale a number to 0..1 (if everything is equal, return 0.5)."""
    if high == low:
        return 0.5
    return (value - low) / (high - low)


# ------------------------------------------------------------ main function
def analyse_products(products):
    """Add price/quality/specs info to every product (used by the whole site)."""
    if not products:
        return []
    average_rating = sum(p["rating"] for p in products) / len(products)
    spec_max = {k: max(p[k] for p in products) or 1
                for k in ("ram_gb", "storage_gb", "camera_mp", "battery_mah")}
    result = []
    for p in products:
        item = dict(p)
        item["low_price"], item["low_platform"] = lowest_price(p)
        item["adjusted_rating"] = round(adjusted_rating(p["rating"], p["review_count"], average_rating), 2)
        item["quality"] = quality_label(item["adjusted_rating"], p["seller_score"])
        # specs score: average of 4 specs, each compared with the best in the list
        item["specs_score"] = sum(p[k] / spec_max[k] for k in spec_max) / 4
        result.append(item)
    return result


def recommend(products, budget, priority="balanced", min_ram=0, top_n=3):
    """
    Return a dictionary with the best product, a ranked list and reasons.
    `products` is a list of dictionaries from the database.
    """
    if priority not in WEIGHTS:
        priority = "balanced"
    weights = WEIGHTS[priority]

    analysed = analyse_products(products)
    # Step 1: budget and RAM filter
    candidates = [p for p in analysed
                  if p["low_price"] and p["low_price"] <= budget and p["ram_gb"] >= min_ram]
    if not candidates:
        return {"best": None, "ranking": [], "message": "No product fits this budget. Try a higher budget or lower RAM."}

    # Step 2: scores between 0 and 1
    cheapest = min(p["low_price"] for p in candidates)
    dearest = max(p["low_price"] for p in candidates)
    quality_low = min(p["adjusted_rating"] for p in candidates)
    quality_high = max(p["adjusted_rating"] for p in candidates)
    avg_specs = sum(p["specs_score"] for p in candidates) / len(candidates)

    for p in candidates:
        parts = {
            "price": 1 - scale(p["low_price"], cheapest, dearest),
            "quality": scale(p["adjusted_rating"], quality_low, quality_high),
            "specs": p["specs_score"],
            "seller": p["seller_score"] / 5,
        }
        # Step 3 + 4: weighted sum
        p["parts"] = {k: round(v * 100) for k, v in parts.items()}
        p["score"] = round(sum(parts[k] * weights[k] for k in parts) * 100, 1)
        p["reasons"] = build_reasons(p, budget, cheapest, avg_specs, candidates)

    # Step 5: rank
    ranking = sorted(candidates, key=lambda p: p["score"], reverse=True)
    for position, p in enumerate(ranking, start=1):
        p["rank"] = position

    best = ranking[0]
    gap = best["score"] - ranking[1]["score"] if len(ranking) > 1 else 100
    confidence = "High" if gap >= 8 else "Medium" if gap >= 3 else "Low (close contest)"

    return {
        "best": best,
        "ranking": ranking[:top_n] if top_n else ranking,
        "all_ranked": len(ranking),
        "confidence": confidence,
        "priority": PRIORITY_LABELS[priority],
        "weights": weights,
        "message": f"Best match for a budget of ₹{budget:,} with priority '{PRIORITY_LABELS[priority]}'.",
    }


def build_reasons(p, budget, cheapest, avg_specs, candidates):
    """Create understandable reasons for a recommendation."""
    reasons = []
    saving = budget - p["low_price"]
    reasons.append(f"Lowest price is ₹{p['low_price']:,} on {p['low_platform']}, "
                   f"₹{saving:,} under your budget.")
    if p["low_price"] == cheapest:
        reasons.append("It is the cheapest option within your budget.")
    reasons.append(f"Customer rating is {p['rating']}/5 from {p['review_count']:,} reviews "
                   f"(adjusted rating {p['adjusted_rating']}). Quality check: {p['quality']}.")
    if p["specs_score"] > avg_specs:
        reasons.append(f"Specifications are above average: {p['ram_gb']} GB RAM, "
                       f"{p['storage_gb']} GB storage, {p['camera_mp']} MP camera.")
    else:
        reasons.append(f"Specifications are modest: {p['ram_gb']} GB RAM, {p['storage_gb']} GB storage.")
    if p["seller_score"] >= 4.4:
        reasons.append(f"Seller reliability is high ({p['seller_score']}/5).")
    elif p["seller_score"] < 4.0:
        reasons.append(f"Seller reliability is only {p['seller_score']}/5, so check the seller before buying.")
    return reasons


def budget_tiers(products, budgets=(15000, 20000, 25000, 30000, 40000)):
    """Best product for several budgets (used for the 'by budget' table)."""
    rows = []
    for b in budgets:
        result = recommend(products, b, "balanced", top_n=1)
        if result["best"]:
            rows.append({"budget": b, "name": result["best"]["name"], "score": result["best"]["score"]})
    return rows
