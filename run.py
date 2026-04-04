from app import create_app
from dotenv import load_dotenv
import os

load_dotenv()  # load env vars dari .env

app = create_app()


if __name__ == "__main__":
    debug_mode = os.getenv('FLASK_DEBUG', '').lower() in {'1', 'true', 'yes'}
    app.run(debug=debug_mode)
