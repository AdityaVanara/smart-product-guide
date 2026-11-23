"""
stats_analysis.py  -  Probability & Statistics on the real database records.

Every number on the dashboard comes from an SQL query or a calculation here.
Nothing is typed in by hand, so charts update when new records are added.
(The file is not called statistics.py because Python already has that module.)
"""
import math
import statistics

from ai.recommendation import PLATFORMS, PRIORITY_LABELS


def percent(part, total):
    """part / total as a percentage with 1 decimal (0 if total is 0)."""
    return round(part * 100 / total, 1) if total else 0


def count_by(conn, sql):
    """Run a 'SELECT label, COUNT(*) ... GROUP BY' query and return a list of [label, count]."""
    return [[row[0], row[1]] for row in conn.execute(sql).fetchall()]


def add_percent(pairs):
    """[[label, count]] -> [{label, count, percent}]"""
    total = sum(c for _, c in pairs)
    return [{"label": l, "count": c, "percent": percent(c, total)} for l, c in pairs]


def pearson(xs, ys):
    """Correlation coefficient r between two lists (-1 to +1)."""
    if len(xs) < 3:
        return None
    mx, my = statistics.mean(xs), statistics.mean(ys)
    top = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    bottom = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    return round(top / bottom, 2) if bottom else None


def get_stats(conn):
    """Collect every statistic for the dashboard in one dictionary."""
    s = {}

    # ---- totals
    s["total_products"] = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    s["total_surveys"] = conn.execute("SELECT COUNT(*) FROM survey_responses").fetchone()[0]
    s["total_feedback"] = conn.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
    s["total_preferences"] = conn.execute("SELECT COUNT(*) FROM preferences").fetchone()[0]
    s["demo_records"] = sum(conn.execute(f"SELECT COUNT(*) FROM {t} WHERE is_sample = 1").fetchone()[0]
                            for t in ("products", "survey_responses", "feedback"))

    # ---- survey: percentages
    s["platforms"] = add_percent(count_by(conn,
        "SELECT main_platform, COUNT(*) FROM survey_responses GROUP BY main_platform ORDER BY COUNT(*) DESC"))
    s["most_popular_platform"] = s["platforms"][0]["label"] if s["platforms"] else "No data"
    s["difficulties"] = add_percent(count_by(conn,
        "SELECT difficulty, COUNT(*) FROM survey_difficulties GROUP BY difficulty ORDER BY COUNT(*) DESC"))
    # difficulty percentage = share of RESPONDENTS (one person can pick many)
    for d in s["difficulties"]:
        d["percent"] = percent(d["count"], s["total_surveys"])
    s["most_common_difficulty"] = s["difficulties"][0]["label"] if s["difficulties"] else "No data"
    s["helpful_features"] = add_percent(count_by(conn,
        "SELECT helpful_feature, COUNT(*) FROM survey_responses GROUP BY helpful_feature ORDER BY COUNT(*) DESC"))
    s["age_groups"] = add_percent(count_by(conn,
        "SELECT age_group, COUNT(*) FROM survey_responses GROUP BY age_group ORDER BY age_group"))
    s["delays"] = add_percent(count_by(conn,
        "SELECT delays_purchase, COUNT(*) FROM survey_responses GROUP BY delays_purchase"))

    # ---- probability
    delay = conn.execute(
        "SELECT COUNT(*) FROM survey_responses WHERE delays_purchase IN ('Yes','Sometimes')").fetchone()[0]
    s["p_delay"] = percent(delay, s["total_surveys"])
    # conditional probability  P(delay | quality doubts) = P(A and B) / P(B)
    doubt = conn.execute(
        "SELECT COUNT(DISTINCT response_id) FROM survey_difficulties WHERE difficulty = 'Quality doubts'").fetchone()[0]
    both = conn.execute(
        """SELECT COUNT(DISTINCT d.response_id) FROM survey_difficulties d
           JOIN survey_responses r ON r.id = d.response_id
           WHERE d.difficulty = 'Quality doubts' AND r.delays_purchase IN ('Yes','Sometimes')""").fetchone()[0]
    s["p_delay_given_doubt"] = percent(both, doubt)

    # ---- customer preferences
    s["priorities"] = add_percent(count_by(conn,
        "SELECT priority, COUNT(*) FROM preferences GROUP BY priority ORDER BY COUNT(*) DESC"))
    for item in s["priorities"]:  # show friendly names instead of database keys
        item["label"] = PRIORITY_LABELS.get(item["label"], item["label"])
    row = conn.execute("SELECT AVG(budget), MIN(budget), MAX(budget) FROM preferences").fetchone()
    s["avg_budget"] = round(row[0]) if row[0] else 0
    s["budget_range"] = [row[1] or 0, row[2] or 0]
    budgets = [r[0] for r in conn.execute("SELECT budget FROM preferences").fetchall()]
    s["median_budget"] = round(statistics.median(budgets)) if budgets else 0
    s["top_priority"] = s["priorities"][0]["label"] if s["priorities"] else "No data"

    # ---- products
    products = [dict(r) for r in conn.execute("SELECT * FROM products").fetchall()]
    s["avg_rating"] = round(statistics.mean(p["rating"] for p in products), 2) if products else 0
    s["avg_prices"] = []
    for platform, column in PLATFORMS.items():
        values = [p[column] for p in products if p[column]]
        s["avg_prices"].append({"label": platform, "value": round(statistics.mean(values)) if values else 0})
    lows = [min(p[c] for c in PLATFORMS.values() if p[c]) for p in products if any(p[c] for c in PLATFORMS.values())]
    s["price_mean"] = round(statistics.mean(lows)) if lows else 0
    s["price_median"] = round(statistics.median(lows)) if lows else 0
    s["price_std"] = round(statistics.pstdev(lows)) if len(lows) > 1 else 0
    s["price_rating_r"] = pearson([min(p[c] for c in PLATFORMS.values() if p[c]) for p in products if any(p[c] for c in PLATFORMS.values())],
                                  [p["rating"] for p in products if any(p[c] for c in PLATFORMS.values())])
    # how often is each platform the cheapest?
    wins = {name: 0 for name in PLATFORMS}
    for p in products:
        available = {n: p[c] for n, c in PLATFORMS.items() if p[c]}
        if available:
            wins[min(available, key=available.get)] += 1
    s["cheapest_platform_counts"] = [{"label": k, "value": v} for k, v in wins.items()]
    s["product_ratings"] = [{"label": p["name"], "value": p["rating"]} for p in
                            sorted(products, key=lambda p: p["rating"], reverse=True)]
    s["price_by_product"] = [{"label": p["name"], "value": min(p[c] for c in PLATFORMS.values() if p[c])}
                             for p in products if any(p[c] for c in PLATFORMS.values())]

    # ---- feedback
    row = conn.execute("SELECT AVG(rating) FROM feedback").fetchone()
    s["avg_feedback_rating"] = round(row[0], 2) if row[0] else 0
    star_counts = {r[0]: r[1] for r in conn.execute("SELECT rating, COUNT(*) FROM feedback GROUP BY rating")}
    s["feedback_stars"] = [{"label": f"{n} star", "value": star_counts.get(n, 0)} for n in range(5, 0, -1)]
    positive = sum(c for stars, c in star_counts.items() if stars >= 4)
    s["feedback_positive_pct"] = percent(positive, s["total_feedback"])
    s["feedback_features"] = add_percent(count_by(conn,
        "SELECT helpful_feature, COUNT(*) FROM feedback WHERE helpful_feature != '' GROUP BY helpful_feature ORDER BY COUNT(*) DESC"))
    return s
