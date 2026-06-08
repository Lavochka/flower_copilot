from flask import Flask, render_template, request, jsonify
from models import db, Card
import os
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='/Users/rasul_gadjiyev/gulcard_project/static')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
db.init_app(app)

BOT_TOKEN = os.getenv("BOT_TOKEN")

def send_telegram_notification(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text})
    except Exception as e:
        print(f"Error sending notification: {e}")

@app.route('/card/<card_id>')
def view_card(card_id):
    card = Card.query.get_or_404(card_id)
    
    if not card.is_viewed:
        card.is_viewed = True
        db.session.commit()
        send_telegram_notification(
            card.sender_id, 
            f"🔔 Вашу открытку «{card.title}» только что отсканировали и открыли!"
        )
    
    return render_template('card.html', card=card)

@app.route('/card/<card_id>/reply', methods=['POST'])
def reply_card(card_id):
    card = Card.query.get_or_404(card_id)
    reply_text = request.form.get('reply')
    if reply_text:
        card.reply_text = reply_text
        db.session.commit()
        send_telegram_notification(
            card.sender_id, 
            f"💌 Получен ответ на вашу открытку «{card.title}»:\n\n{reply_text}"
        )
        return jsonify({"status": "ok", "message": "Ответ отправлен!"})
    return jsonify({"status": "error"}), 400

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000)
