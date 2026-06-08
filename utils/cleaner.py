import os
import time
from datetime import datetime, timedelta
from models import db, Card
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
db.init_app(app)

def cleanup_old_cards():
    with app.app_context():
        # Находим открытки, срок которых истек
        now = datetime.utcnow()
        expired_cards = Card.query.filter(Card.expires_at <= now).all()
        
        for card in expired_cards:
            # Удаляем медиа-файл
            if card.media_path and os.path.exists(card.media_path):
                try:
                    os.remove(card.media_path)
                    print(f"Deleted media: {card.media_path}")
                except Exception as e:
                    print(f"Error deleting file {card.media_path}: {e}")
            
            # Удаляем QR-код
            qr_path = f"static/qrcodes/{card.id}.png"
            if os.path.exists(qr_path):
                os.remove(qr_path)
            
            # Удаляем запись из БД
            db.session.delete(card)
        
        db.session.commit()
        print(f"Cleanup finished at {now}. Deleted {len(expired_cards)} cards.")

if __name__ == "__main__":
    cleanup_old_cards()
