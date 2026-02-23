import os

from app import create_app


app = create_app()

 
if __name__ == '__main__':
    debug_enabled = os.getenv('FLASK_DEBUG', '0') == '1' or os.getenv('FLASK_ENV') == 'development'
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=debug_enabled, use_reloader=False)
