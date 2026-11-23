"""
database.py  -  SQLite database for the Smart Product Guide.

This file does three things:
  1. get_db()  opens a connection to the SQLite file.
  2. init_db() creates the tables (if they do not exist yet).
  3. seed_demo_data() adds SAMPLE records so the site is not empty on first run.

All sample rows have is_sample = 1, so they are always labelled as demo data.
"""
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "shopping.db")


def get_db():
    """Open a connection. Rows can be used like dictionaries (row["name"])."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")  # needed for ON DELETE CASCADE
    return conn


# ---------------------------------------------------------------- tables
SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    brand           TEXT    DEFAULT '',
    category        TEXT    DEFAULT 'Phones',
    ram_gb          INTEGER DEFAULT 0,
    storage_gb      INTEGER DEFAULT 0,
    camera_mp       INTEGER DEFAULT 0,
    battery_mah     INTEGER DEFAULT 0,
    price_amazon    INTEGER,            -- NULL means "not sold here"
    price_flipkart  INTEGER,
    price_meesho    INTEGER,
    rating          REAL    NOT NULL,   -- average customer rating (0-5)
    review_count    INTEGER DEFAULT 0,
    seller_score    REAL    DEFAULT 3,  -- seller reliability (0-5)
    is_sample       INTEGER DEFAULT 0,  -- 1 = demo data, NOT a real price/review
    created_at      TEXT    DEFAULT CURRENT_TIMESTAMP
);

-- Shortlist: the products a customer picked for comparison.
CREATE TABLE IF NOT EXISTS shortlist (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL UNIQUE,
    added_at   TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS survey_responses (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT DEFAULT '',
    age_group       TEXT NOT NULL,
    occupation      TEXT NOT NULL,
    main_platform   TEXT NOT NULL,     -- Amazon / Flipkart / Meesho / Other
    delays_purchase TEXT NOT NULL,     -- Yes / Sometimes / No
    helpful_feature TEXT NOT NULL,
    comment         TEXT DEFAULT '',
    is_sample       INTEGER DEFAULT 0,
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP
);

-- One survey response can have MANY difficulties (one-to-many relationship).
CREATE TABLE IF NOT EXISTS survey_difficulties (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    response_id INTEGER NOT NULL,
    difficulty  TEXT NOT NULL,
    FOREIGN KEY (response_id) REFERENCES survey_responses(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS feedback (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT DEFAULT '',
    rating        INTEGER NOT NULL,    -- 1 to 5 stars
    helpful_feature TEXT DEFAULT '',
    comment       TEXT DEFAULT '',
    is_sample     INTEGER DEFAULT 0,
    created_at    TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Customer preferences: saved from the survey and from the AI page.
CREATE TABLE IF NOT EXISTS preferences (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    response_id INTEGER,               -- links to a survey response (optional)
    budget      INTEGER NOT NULL,
    priority    TEXT NOT NULL,         -- balanced / price / quality / performance / seller
    source      TEXT DEFAULT 'survey', -- 'survey' or 'ai'
    is_sample   INTEGER DEFAULT 0,
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (response_id) REFERENCES survey_responses(id) ON DELETE CASCADE
);
"""


def init_db():
    """Create the database file and tables, then add demo data once."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db()
    conn.executescript(SCHEMA)
    conn.commit()
    if conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
        seed_demo_data(conn)
    conn.close()


# ------------------------------------------------------------ demo data
# (name, brand, ram, storage, camera, battery, amazon, flipkart, meesho, rating, reviews, seller)
SAMPLE_PRODUCTS = [
    ("Nova X1",   "Nova",  6, 128, 48, 5000, 22499, 22999, 23200, 3.9, 1820, 3.8),
    ("Pulse 5G",  "Pulse", 8, 128, 50, 5000, 23999, 24499, 23500, 4.6, 3410, 4.7),
    ("Orbit Pro", "Orbit", 8, 256, 64, 5500, 24999, 24499, 25800, 4.4, 2650, 4.4),
    ("Zen Lite",  "Zen",   4,  64, 13, 5000, 14999, 15499, 14200, 4.0, 5120, 4.1),
    ("Spark Max", "Spark", 12, 256, 108, 5000, 31999, 30999, 32500, 4.5, 1980, 4.5),
    ("Aero Neo",  "Aero",  6, 128, 50, 4500, 18999, 19499, 18500, 4.2, 2210, 3.9),
]

# (age, occupation, platform, delays, helpful feature, [difficulties], budget, priority, comment)
SAMPLE_SURVEYS = [
    ("18-25", "Student", "Amazon", "Sometimes", "Reliable reviews", ["Quality doubts", "Trusting reviews"], 20000, "quality", "Fake reviews confuse me."),
    ("18-25", "Student", "Flipkart", "Yes", "Price comparison", ["Different prices", "Too many choices"], 15000, "price", ""),
    ("18-25", "Student", "Meesho", "Sometimes", "Compare specs", ["Quality doubts", "Photos differ from product"], 12000, "price", "Photos do not match."),
    ("26-35", "Employed", "Amazon", "Sometimes", "Reliable reviews", ["Quality doubts", "Comparing specs"], 30000, "balanced", ""),
    ("26-35", "Employed", "Flipkart", "No", "Seller reliability", ["Finding good sellers"], 25000, "seller", ""),
    ("18-25", "Student", "Amazon", "Yes", "Details in one place", ["Too many choices", "Comparing specs"], 22000, "performance", "Twelve tabs open!"),
    ("36-50", "Employed", "Amazon", "Sometimes", "Reliable reviews", ["Trusting reviews", "Quality doubts"], 35000, "quality", ""),
    ("18-25", "Student", "Flipkart", "Sometimes", "Compare specs", ["Comparing specs", "Different prices"], 18000, "performance", ""),
    ("26-35", "Self-employed", "Meesho", "No", "Price comparison", ["Different prices"], 10000, "price", ""),
    ("18-25", "Student", "Amazon", "Yes", "Reliable reviews", ["Quality doubts", "Finding good sellers"], 24000, "balanced", ""),
    ("26-35", "Homemaker", "Flipkart", "Sometimes", "Verified photos", ["Photos differ from product", "Quality doubts"], 15000, "quality", ""),
    ("18-25", "Student", "Amazon", "Sometimes", "Details in one place", ["Too many choices", "Quality doubts"], 25000, "balanced", ""),
]

SAMPLE_FEEDBACK = [
    ("Demo user 1", 5, "Price comparison", "Seeing all three prices together saved time."),
    ("Demo user 2", 4, "Reliable reviews", "Good idea. I would like more products."),
    ("Demo user 3", 4, "Spec comparison", "Easy to compare RAM and storage."),
    ("Demo user 4", 3, "All details in one place", "Useful, but the data should be live."),
]


def seed_demo_data(conn):
    """Insert SAMPLE rows (is_sample = 1). The dashboard has a button to delete them."""
    for p in SAMPLE_PRODUCTS:
        conn.execute(
            """INSERT INTO products (name, brand, ram_gb, storage_gb, camera_mp, battery_mah,
               price_amazon, price_flipkart, price_meesho, rating, review_count, seller_score, is_sample)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,1)""", p)

    for age, job, platform, delays, feature, difficulties, budget, priority, comment in SAMPLE_SURVEYS:
        cur = conn.execute(
            """INSERT INTO survey_responses
               (name, age_group, occupation, main_platform, delays_purchase, helpful_feature, comment, is_sample)
               VALUES ('Demo respondent',?,?,?,?,?,?,1)""",
            (age, job, platform, delays, feature, comment))
        response_id = cur.lastrowid
        for d in difficulties:
            conn.execute("INSERT INTO survey_difficulties (response_id, difficulty) VALUES (?,?)",
                         (response_id, d))
        conn.execute(
            "INSERT INTO preferences (response_id, budget, priority, source, is_sample) VALUES (?,?,?,'survey',1)",
            (response_id, budget, priority))

    for name, rating, feature, comment in SAMPLE_FEEDBACK:
        conn.execute(
            "INSERT INTO feedback (name, rating, helpful_feature, comment, is_sample) VALUES (?,?,?,?,1)",
            (name, rating, feature, comment))
    conn.commit()


if __name__ == "__main__":
    # Run  python database.py  to (re)create the database by hand.
    init_db()
    print("Database ready at", DB_PATH)
