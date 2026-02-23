# Fake News Lab (Flask)

Small Flask app for classifying news text or URLs with a local HuggingFace model. Results are persisted to MongoDB for later BI/analytics.

## Features
- Email/password auth (Flask-Login)
- Submit raw text or a news URL; URL content is scraped before inference
- HuggingFace fake-news classifier runs locally
- Results + metadata saved to MongoDB (user-scoped)
- Dashboard with counts and history list

## Quickstart
1. Python 3.10+ recommended.
2. Create env: `python -m venv .venv` and `./.venv/Scripts/activate` (Windows).
3. Install deps: `pip install -r requirements.txt`.
4. Copy `.env.example` to `.env` and set values:
   - `SECRET_KEY` any random string
   - `MONGO_URI` MongoDB Atlas connection string
   - `MONGO_DB_NAME` database to use
   - `HUGGINGFACE_MODEL` optional override (defaults to mrm8488/bert-tiny-finetuned-fake-news-detection)
5. First run will download the model; stay online once. Then start: `python run.py` and open http://localhost:5000.

## How it works
- `app/services/classifier.py` loads a text-classification pipeline and maps labels to Fake/Real.
- `app/utils/scraper.py` fetches article text from a URL using readability and BeautifulSoup.
- Classified documents go into `articles` collection with fields like `user_id`, `input_type`, `model_label`, `model_score`, `created_at`, and `meta` (URL/title/status).

## Structure
- `app/auth` auth routes
- `app/main` landing, dashboard, classify, history, about
- `app/templates` Jinja templates
- `app/static` CSS/JS

## Notes
- Keep the model small for laptops; the default tiny model runs on CPU. Swap to a larger HF model if you have GPU.
- Add HTTPS, stronger password policy, and CSRF protection before production use.
