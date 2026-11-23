"""
app.py  -  Flask backend for the Smart Product Guide (Python Programming).

Two kinds of routes:
  * Page routes  (/, /products ...)  -> return an HTML page from templates/
  * API routes   (/api/...)          -> return JSON; JavaScript calls them

CRUD = Create (POST), Read (GET), Update (PUT), Delete (DELETE)
"""
import csv
import io

from flask import Flask, Response, jsonify, render_template, request

from ai.recommendation import PRIORITY_LABELS, analyse_products, budget_tiers, recommend
from database import get_db, init_db
from stats_analysis import get_stats

app = Flask(__name__)
init_db()  # create tables + demo data the first time the app starts

PLATFORM_COLUMNS = ["price_amazon", "price_flipkart", "price_meesho"]
FEATURES = ["Reliable reviews", "Compare specs", "Details in one place",
            "Price comparison", "Seller reliability", "Verified photos"]


# ------------------------------------------------------------ small helpers
def rows_to_list(rows):
    return [dict(r) for r in rows]


def error(message, code=400):
    return jsonify({"error": message}), code


def to_int(value, default=None):
    """Convert text to a whole number. Empty text gives `default`."""
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def clean_product(data):
    """Validate product form data. Returns (product_dict, error_message)."""
    name = str(data.get("name", "")).strip()
    if not name:
        return None, "Product name is required."
    rating = data.get("rating")
    try:
        rating = float(rating)
    except (TypeError, ValueError):
        return None, "Rating must be a number between 0 and 5."
    if not 0 <= rating <= 5:
        return None, "Rating must be between 0 and 5."
    product = {
        "name": name[:60],
        "brand": str(data.get("brand", "")).strip()[:40],
        "ram_gb": to_int(data.get("ram_gb"), 0),
        "storage_gb": to_int(data.get("storage_gb"), 0),
        "camera_mp": to_int(data.get("camera_mp"), 0),
        "battery_mah": to_int(data.get("battery_mah"), 0),
        "rating": rating,
        "review_count": to_int(data.get("review_count"), 0),
        "seller_score": min(5, max(0, float(data.get("seller_score") or 3))),
    }
    for column in PLATFORM_COLUMNS:
        product[column] = to_int(data.get(column))  # None when empty
    if not any(product[c] for c in PLATFORM_COLUMNS):
        return None, "Enter a price for at least one platform."
    if any(product[c] is not None and product[c] <= 0 for c in PLATFORM_COLUMNS):
        return None, "Prices must be positive numbers."
    return product, None


def load_products(conn):
    return rows_to_list(conn.execute("SELECT * FROM products ORDER BY id").fetchall())


# ------------------------------------------------------------ page routes
@app.route("/")
def home():
    return render_template("index.html", page="home")


@app.route("/products")
def products_page():
    return render_template("products.html", page="products")


@app.route("/comparison")
def comparison_page():
    return render_template("comparison.html", page="comparison")


@app.route("/feedback")
def feedback_page():
    return render_template("feedback.html", page="feedback", features=FEATURES)


@app.route("/recommendations")
def recommendations_page():
    return render_template("recommendations.html", page="recommendations", priorities=PRIORITY_LABELS)


@app.route("/about")
def about_page():
    return render_template("about.html", page="about")


# ------------------------------------------------------------ products API
@app.route("/api/products", methods=["GET"])
def list_products():
    """Read: search, budget filter and sorting are done here in Python."""
    conn = get_db()
    products = analyse_products(load_products(conn))
    conn.close()

    text = request.args.get("q", "").strip().lower()
    budget = to_int(request.args.get("budget"))
    if text:
        products = [p for p in products if text in p["name"].lower() or text in p["brand"].lower()]
    if budget:
        products = [p for p in products if p["low_price"] and p["low_price"] <= budget]

    # "Best match" uses the balanced AI score, so we rank with the AI module.
    sort = request.args.get("sort", "price")
    if sort == "rating":
        products.sort(key=lambda p: p["rating"], reverse=True)
    elif sort == "match":
        ranked = recommend(products, budget or 10 ** 9, "balanced", top_n=0)["ranking"]
        scores = {p["id"]: p["score"] for p in ranked}
        for p in products:
            p["match_score"] = scores.get(p["id"], 0)
        products.sort(key=lambda p: p["match_score"], reverse=True)
    else:
        products.sort(key=lambda p: p["low_price"] or 10 ** 9)

    # badges (computed over the filtered list)
    if products:
        lowest = min(products, key=lambda p: p["low_price"] or 10 ** 9)["id"]
        top = max(products, key=lambda p: p["rating"])["id"]
        ranked = recommend(products, budget or 10 ** 9, "balanced", top_n=1)
        best = ranked["best"]["id"] if ranked["best"] else None
        for p in products:
            p["badges"] = [b for b, pid in (("Lowest price", lowest), ("Top rated", top), ("Best match", best))
                           if pid == p["id"]]
    return jsonify(products)


@app.route("/api/products", methods=["POST"])
def add_product():
    product, problem = clean_product(request.get_json(silent=True) or {})
    if problem:
        return error(problem)
    conn = get_db()
    columns = ", ".join(product)
    marks = ", ".join("?" for _ in product)
    cur = conn.execute(f"INSERT INTO products ({columns}) VALUES ({marks})", list(product.values()))
    conn.commit()
    conn.close()
    return jsonify({"id": cur.lastrowid}), 201


@app.route("/api/products/<int:product_id>", methods=["PUT"])
def edit_product(product_id):
    product, problem = clean_product(request.get_json(silent=True) or {})
    if problem:
        return error(problem)
    conn = get_db()
    changes = ", ".join(f"{c} = ?" for c in product)
    # an edited product is no longer "sample" data: the owner has checked it
    cur = conn.execute(f"UPDATE products SET {changes}, is_sample = 0 WHERE id = ?",
                       list(product.values()) + [product_id])
    conn.commit()
    conn.close()
    return jsonify({"updated": cur.rowcount}) if cur.rowcount else error("Product not found.", 404)


@app.route("/api/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    conn = get_db()
    cur = conn.execute("DELETE FROM products WHERE id = ?", (product_id,))  # shortlist rows cascade
    conn.commit()
    conn.close()
    return jsonify({"deleted": cur.rowcount}) if cur.rowcount else error("Product not found.", 404)


# ------------------------------------------------------------ shortlist + comparison
@app.route("/api/shortlist", methods=["GET"])
def get_shortlist():
    conn = get_db()
    ids = [r[0] for r in conn.execute("SELECT product_id FROM shortlist ORDER BY id").fetchall()]
    conn.close()
    return jsonify(ids)


@app.route("/api/shortlist/<int:product_id>", methods=["POST"])
def add_to_shortlist(product_id):
    conn = get_db()
    if not conn.execute("SELECT 1 FROM products WHERE id = ?", (product_id,)).fetchone():
        conn.close()
        return error("Product not found.", 404)
    if conn.execute("SELECT COUNT(*) FROM shortlist").fetchone()[0] >= 3:
        conn.close()
        return error("You can compare up to 3 products. Remove one first.")
    conn.execute("INSERT OR IGNORE INTO shortlist (product_id) VALUES (?)", (product_id,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True}), 201


@app.route("/api/shortlist/<int:product_id>", methods=["DELETE"])
def remove_from_shortlist(product_id):
    conn = get_db()
    conn.execute("DELETE FROM shortlist WHERE product_id = ?", (product_id,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/shortlist", methods=["DELETE"])
def clear_shortlist():
    conn = get_db()
    conn.execute("DELETE FROM shortlist")
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/compare")
def compare():
    """Return the shortlisted products, with the 'winner' of every row."""
    conn = get_db()
    everything = analyse_products(load_products(conn))
    ids = [r[0] for r in conn.execute("SELECT product_id FROM shortlist ORDER BY id").fetchall()]
    conn.close()
    chosen = [p for p in everything if p["id"] in ids]
    chosen.sort(key=lambda p: ids.index(p["id"]))

    best = None
    if chosen:
        result = recommend(chosen, 10 ** 9, "balanced", top_n=0)
        scores = {p["id"]: p["score"] for p in result["ranking"]}
        for p in chosen:
            p["match_score"] = scores.get(p["id"], 0)
        best = max(chosen, key=lambda p: p["match_score"])["id"]
    return jsonify({"products": chosen, "best_match_id": best})


# ------------------------------------------------------------ feedback API
def clean_feedback(data):
    rating = to_int(data.get("rating"), 0)
    if not 1 <= rating <= 5:
        return None, "Choose a star rating from 1 to 5."
    return {"name": str(data.get("name", "")).strip()[:40],
            "rating": rating,
            "helpful_feature": str(data.get("helpful_feature", "")).strip()[:60],
            "comment": str(data.get("comment", "")).strip()[:300]}, None


@app.route("/api/feedback", methods=["GET"])
def list_feedback():
    conn = get_db()
    rows = rows_to_list(conn.execute("SELECT * FROM feedback ORDER BY id DESC").fetchall())
    conn.close()
    return jsonify(rows)


@app.route("/api/feedback", methods=["POST"])
def add_feedback():
    item, problem = clean_feedback(request.get_json(silent=True) or {})
    if problem:
        return error(problem)
    conn = get_db()
    cur = conn.execute("INSERT INTO feedback (name, rating, helpful_feature, comment) VALUES (?,?,?,?)",
                       (item["name"], item["rating"], item["helpful_feature"], item["comment"]))
    conn.commit()
    conn.close()
    return jsonify({"id": cur.lastrowid}), 201


@app.route("/api/feedback/<int:feedback_id>", methods=["PUT"])
def edit_feedback(feedback_id):
    item, problem = clean_feedback(request.get_json(silent=True) or {})
    if problem:
        return error(problem)
    conn = get_db()
    cur = conn.execute(
        "UPDATE feedback SET name=?, rating=?, helpful_feature=?, comment=?, is_sample=0 WHERE id=?",
        (item["name"], item["rating"], item["helpful_feature"], item["comment"], feedback_id))
    conn.commit()
    conn.close()
    return jsonify({"updated": cur.rowcount}) if cur.rowcount else error("Feedback not found.", 404)


@app.route("/api/feedback/<int:feedback_id>", methods=["DELETE"])
def delete_feedback(feedback_id):
    conn = get_db()
    cur = conn.execute("DELETE FROM feedback WHERE id = ?", (feedback_id,))
    conn.commit()
    conn.close()
    return jsonify({"deleted": cur.rowcount}) if cur.rowcount else error("Feedback not found.", 404)


@app.route("/api/feedback", methods=["DELETE"])
def delete_all_feedback():
    conn = get_db()
    conn.execute("DELETE FROM feedback")
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/feedback/export.csv")
def export_feedback():
    """Download all feedback as a CSV file (existing feature, now from the database)."""
    conn = get_db()
    rows = conn.execute("SELECT name, rating, helpful_feature, comment, created_at FROM feedback ORDER BY id").fetchall()
    conn.close()
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["name", "rating", "helpful_feature", "comment", "date"])
    writer.writerows([list(r) for r in rows])
    return Response(out.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=feedback.csv"})


# ------------------------------------------------------------ AI + statistics API
@app.route("/api/recommend", methods=["POST"])
def api_recommend():
    data = request.get_json(silent=True) or {}
    budget = to_int(data.get("budget"), 0)
    if budget <= 0:
        return error("Enter a budget in rupees.")
    priority = data.get("priority") if data.get("priority") in PRIORITY_LABELS else "balanced"
    min_ram = to_int(data.get("min_ram"), 0)

    conn = get_db()
    result = recommend(load_products(conn), budget, priority, min_ram, top_n=3)
    # save the customer's preference (used by the statistics page)
    conn.execute("INSERT INTO preferences (budget, priority, source) VALUES (?,?,'ai')", (budget, priority))
    conn.commit()
    result["tiers"] = budget_tiers(load_products(conn))
    conn.close()
    return jsonify(result)


@app.route("/api/tiers")
def api_tiers():
    """Best product for several budgets (does not save anything)."""
    conn = get_db()
    tiers = budget_tiers(load_products(conn))
    conn.close()
    return jsonify(tiers)


@app.route("/api/stats")
def api_stats():
    conn = get_db()
    stats = get_stats(conn)
    conn.close()
    return jsonify(stats)


@app.route("/api/demo-data", methods=["DELETE"])
def delete_demo_data():
    """Remove every record marked as sample/demo data."""
    conn = get_db()
    for table in ("products", "survey_responses", "feedback"):
        conn.execute(f"DELETE FROM {table} WHERE is_sample = 1")
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True)
