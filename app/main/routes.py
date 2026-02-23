from datetime import datetime
from urllib.parse import urlparse
from flask import Blueprint, render_template, request, current_app, redirect, url_for, flash
from flask_login import login_required, current_user

from ..services.classifier import classify_text
from ..utils.scraper import fetch_article_text


main_bp = Blueprint('main', __name__, template_folder='../templates')


@main_bp.route('/')
def landing():
    db = current_app.mongo_client[current_app.config['MONGO_DB_NAME']]
    articles = list(db.articles.find({}, {'article_text': 1, 'model_label': 1, 'model_score': 1, 'meta': 1, 'created_at': 1}).sort('created_at', -1).limit(6))

    # Top unreliable sources (client-side domain parsing to avoid Mongo $function dependency)
    recent_fake = list(db.articles.find({'model_label': 'Fake', 'meta.url': {'$exists': True, '$ne': None}}, {'meta.url': 1}).sort('created_at', -1).limit(200))
    counts = {}
    for doc in recent_fake:
        url = doc.get('meta', {}).get('url')
        try:
            domain = urlparse(url).netloc
        except Exception:  # noqa: BLE001
            domain = ''
        if not domain:
            continue
        counts[domain] = counts.get(domain, 0) + 1
    top_sources = sorted(([{'domain': d, 'count': c} for d, c in counts.items()]), key=lambda x: x['count'], reverse=True)[:6]

    return render_template('landing.html', articles=articles, top_sources=top_sources)


@main_bp.route('/dashboard')
@login_required
def dashboard():
    db = current_app.mongo_client[current_app.config['MONGO_DB_NAME']]
    collection = db.articles
    count_user = collection.count_documents({'user_id': current_user.id})
    count_all = collection.estimated_document_count()
    last_doc = collection.find_one({'user_id': current_user.id}, sort=[('created_at', -1)])

    # Label distribution for user
    pipeline_user = [
        {'$match': {'user_id': current_user.id}},
        {'$group': {'_id': '$model_label', 'count': {'$sum': 1}}},
    ]
    label_counts = {doc['_id']: doc['count'] for doc in collection.aggregate(pipeline_user)}
    fake_share = 0.0
    total_labels = sum(label_counts.values())
    if total_labels:
        fake_share = round(label_counts.get('Fake', 0) / total_labels * 100, 1)

    return render_template('dashboard.html', count_user=count_user, count_all=count_all, last_doc=last_doc, fake_share=fake_share, label_counts=label_counts)


@main_bp.route('/history')
@login_required
def history():
    db = current_app.mongo_client[current_app.config['MONGO_DB_NAME']]
    docs = list(db.articles.find({'user_id': current_user.id}).sort('created_at', -1).limit(50))
    return render_template('history.html', docs=docs)


@main_bp.route('/classify', methods=['GET', 'POST'])
@login_required
def classify():
    if request.method == 'POST':
        input_type = request.form.get('input_type') or 'text'
        raw_text = (request.form.get('article_text') or '').strip()
        url_value = (request.form.get('article_url') or '').strip()

        if input_type == 'url':
            if not url_value:
                flash('Provide a URL to analyze.', 'error')
                return render_template('classify.html')
            article_text, scrape_meta = fetch_article_text(url_value)
        else:
            article_text, scrape_meta = raw_text, {'url': None}

        if not article_text:
            msg = scrape_meta.get('error') if scrape_meta else None
            fallback = 'No text found. The site may block scraping; try another link or paste the text manually.'
            flash(msg or fallback, 'error')
            return render_template('classify.html', url_value=url_value, article_text=article_text, scrape_meta=scrape_meta)

        result = classify_text(article_text)
        if result.get('label') == 'Error':
            flash(f"Model error: {result.get('error', 'Unknown issue')}", 'error')
            return render_template('classify.html', url_value=url_value, article_text=article_text, scrape_meta=scrape_meta)

        db = current_app.mongo_client[current_app.config['MONGO_DB_NAME']]
        doc = {
            'user_id': current_user.id,
            'input_type': input_type,
            'raw_input': url_value if input_type == 'url' else raw_text,
            'article_text': article_text,
            'model_label': result['label'],
            'model_score': result['score'],
            'created_at': datetime.utcnow(),
            'meta': scrape_meta,
        }
        db.articles.insert_one(doc)
        flash('Analysis complete.', 'success')
        return render_template('classify.html', result=result, article_text=article_text, url_value=url_value, scrape_meta=scrape_meta)

    return render_template('classify.html')


@main_bp.route('/about')
def about():
    return render_template('about.html')
