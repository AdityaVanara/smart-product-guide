# Online Shopping Product Selection Problem — Smart Product Guide

A Flask + SQLite website that helps customers compare products from Amazon, Flipkart and Meesho.
It upgrades the original HTML/CSS/JavaScript project (browser localStorage) into a database-connected,
AI-assisted website and shows five subjects in one project.

> **Data notice:** products, prices, ratings and the demo survey/feedback rows marked **Sample / Demo**
> are demo data. They are NOT live marketplace prices or real customer reviews.

## 1. Install
```
cd OnlineShoppingProject
python -m venv venv
venv\Scripts\activate          (Windows)      source venv/bin/activate   (Mac/Linux)
pip install -r requirements.txt
```

## 2. Run
```
python app.py
```
Open http://127.0.0.1:5000 in your browser.
The database file `database/shopping.db` is created automatically on first run
(code: `database.py`; run `python database.py` to create it by hand).
To start again from zero, stop the app and delete `database/shopping.db`.

## 3. Pages
| Page | URL | What it does |
|------|-----|--------------|
| Home | `/` | Problem, original 57-person survey, Design Thinking process, live database numbers |
| Products | `/products` | Add, edit, delete products and prices (CRUD) |
| Compare | `/comparison` | Budget, search, sort, shortlist up to 3, side-by-side table |
| AI picks | `/recommendations` | Budget + priority -> ranked products with reasons |
| Feedback | `/feedback` | Star rating, edit, delete, average, CSV export |
| About | `/about` | Project description and subject mapping |

## 4. Folder structure
```
app.py                 Flask routes (pages + JSON API)
database.py            SQLite connection, tables, demo data
stats_analysis.py      Probability & statistics calculations
ai/recommendation.py   AI scoring and explanations
database/shopping.db   SQLite database
templates/             HTML pages (base.html + one file per page)
static/css/style.css   All styling
static/js/             common.js (helpers + charts) and one JS file per page
```

## 5. How the five subjects are implemented
1. **Design Thinking** – Home page shows Empathize, Define, Ideate, Prototype, Test with problem statement,
   customer needs and idea map. Survey = Empathize, Comparison guide = Prototype, Feedback = Test.
2. **Python Programming** – Flask routes, functions, input validation and CRUD in `app.py`; SQLite code in
   `database.py`; calculations in `stats_analysis.py` and `ai/recommendation.py`.
3. **Web Technology** – HTML templates (Jinja), one responsive CSS file, JavaScript with `fetch` calling the Flask API.
4. **Artificial Intelligence** – `ai/recommendation.py`: a transparent weighted-scoring recommender
   (price, review-adjusted rating, specifications, seller reliability, customer priority). It is not a trained
   model because there is no training dataset; every score and reason is shown.
5. **Probability & Statistics** – percentages, means, median, standard deviation, Pearson correlation,
   probability and conditional probability P(delay | quality doubts), all calculated from database records.

## 6. Database tables
`products`, `shortlist` (-> products), `survey_responses`, `survey_difficulties` (-> survey_responses),
`feedback`, `preferences` (-> survey_responses). Foreign keys use `ON DELETE CASCADE`.
There is no login system, so the shortlist is shared by everyone using the same running copy of the site.
