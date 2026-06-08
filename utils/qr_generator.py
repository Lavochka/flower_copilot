import qrcode
from PIL import Image, ImageDraw
import os
from dotenv import load_dotenv

load_dotenv()

def generate_custom_qr(data, card_id):
    shop_name = os.getenv("SHOP_NAME", "GulCard")
    logo_path = os.getenv("SHOP_LOGO_PATH")
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img_qr = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    
    # Попытка добавить логотип, если он существует
    if logo_path and os.path.exists(logo_path):
        logo = Image.open(logo_path)
        # Масштабируем логотип
        box = (img_qr.size[0] // 4, img_qr.size[1] // 4, img_qr.size[0] * 3 // 4, img_qr.size[1] * 3 // 4)
        logo = logo.resize((box[2] - box[0], box[3] - box[1]))
        img_qr.paste(logo, box)

    qr_file_path = f"static/qrcodes/{card_id}.png"
    img_qr.save(qr_file_path)
    return qr_file_path
