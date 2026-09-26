import os
import re
import cv2
import pytesseract
import pdfkit
import telebot
from smtplib import SMTP
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

BOT_TOKEN = "8684964210:AAEnEEYmoKOuhgavmZLRifH2LS1ep_wy8Rw"
GMAIL_USER = "chathuranga1220gmail.com"
GMAIL_APP_PASS = "adoj fqfu ebgm opyf"
OFFICE_EMAIL = "chaaminy3k@gmail.com"

bot = telebot.TeleBot(BOT_TOKEN)
user_data = {}

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    with open("temp.jpg", 'wb') as new_file:
        new_file.write(downloaded_file)
    
    img = cv2.imread("temp.jpg")
    text = pytesseract.image_to_string(img)
    
    claim_no = re.search(r'2605[A-Z0-9]+', text)
    vehicle_no = re.search(r'NC-[A-Z0-9-]+', text)
    
    chat_id = message.chat.id
    user_data[chat_id] = {
        'claim_no': claim_no.group(0) if claim_no else "2605HOVMC35118",
        'vehicle_no': vehicle_no.group(0) if vehicle_no else "NC-BKJ-9809",
        'policy_no': "5DBVMC000004904",
        'insured_name': "එම්. ආර්. එම්. රිමාස්",
        'address': "නියු කඩඳුගම, පුබ්බෝගම"
    }
    
    msg = bot.reply_to(message, " Screenshot එක හඳුනාගත්තා!\n\nකරුණාකර **දුරකථන අංකය** ලබාදෙන්න:")
    bot.register_next_step_handler(msg, process_phone)

def process_phone(message):
    chat_id = message.chat.id
    user_data[chat_id]['phone'] = message.text
    msg = bot.reply_to(message, "කරුණාකර **ගිණුම් අංකය (Account No)** ලබාදෙන්න:")
    bot.register_next_step_handler(msg, process_account)

def process_account(message):
    chat_id = message.chat.id
    user_data[chat_id]['account'] = message.text
    msg = bot.reply_to(message, "කරුණාකර **රියැදුරුගේ නම (Driver Name)** ලබාදෙන්න:")
    bot.register_next_step_handler(msg, process_driver_and_generate)

def process_driver_and_generate(message):
    chat_id = message.chat.id
    user_data[chat_id]['driver'] = message.text
    
    bot.send_message(chat_id, " සිංහල PDF එක සකසමින් පවති... මොහොතක් රැඳී සිටින්න.")
    
    data = user_data[chat_id]
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'LKLUG', sans-serif; font-size: 15px; padding: 25px; line-height: 1.6; }}
            .header {{ text-align: center; font-weight: bold; font-size: 22px; color: #003366; margin-bottom: 5px; }}
            .sub-header {{ text-align: center; font-size: 16px; font-weight: bold; margin-bottom: 20px; }}
            .box {{ border: 2px solid #003366; padding: 20px; border-radius: 8px; margin-top: 15px; }}
            .field {{ margin-bottom: 12px; }}
            .label {{ font-weight: bold; color: #333; display: inline-block; width: 200px; }}
            .val {{ color: #000; font-size: 17px; font-weight: bold; }}
            .page-break {{ page-break-before: always; }}
        </style>
    </head>
    <body>
        <div class="header">PEOPLE'S INSURANCE PLC</div>
        <div class="sub-header">රථවාහන හිමිකම් අයැදුම - MOTOR CLAIM FORM</div>
        <hr>
        <div class="box">
            <div class="field"><span class="label">ඔප්පු අංකය (Policy No):</span> <span class="val">{data['policy_no']}</span></div>
            <div class="field"><span class="label">හිමිකම් අංකය (Claim No):</span> <span class="val">{data['claim_no']}</span></div>
            <div class="field"><span class="label">වාහනයේ ලි.ප. අංකය:</span> <span class="val">{data['vehicle_no']}</span></div>
            <div class="field"><span class="label">රක්ෂිතයාගේ නම:</span> <span class="val">{data['insured_name']}</span></div>
            <div class="field"><span class="label">තැපැල් ලිපිනය:</span> <span class="val">{data['address']}</span></div>
            <div class="field"><span class="label">දුරකථන අංකය:</span> <span class="val">{data['phone']}</span></div>
            <div class="field"><span class="label">බැංකු ගිණුම් අංකය:</span> <span class="val">{data['account']}</span></div>
            <div class="field"><span class="label">රියැදුරුගේ නම:</span> <span class="val">{data['driver']}</span></div>
        </div>
        
        <div class="page-break"></div>
        
        <div class="header">LETTER OF INDEMNITY</div>
        <hr>
        <p style="text-align: justify; font-family: sans-serif; font-size: 14px;">
        I/We <b>{data['insured_name']}</b> of <b>{data['address']}</b> being the owner (s) of the vehicle bearing Registration No. <b>{data['vehicle_no']}</b> and being the holder (s) of Insurance Policy No. <b>{data['policy_no']}</b> issued by PEOPLE's INSURANCE PLC, hereby confirm that the aforementioned vehicle met with an accident...
        </p>
    </body>
    </html>
    """
    
    pdf_path = "Claim_Form_Filled.pdf"
    options = {'encoding': "UTF-8"}
    pdfkit.from_string(html_content, pdf_path, options=options)
    
    # Send Email
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = OFFICE_EMAIL
    msg['Subject'] = f"Filled Claim Form - {data['vehicle_no']}"
    
    part = MIMEBase('application', "octet-stream")
    part.set_payload(open(pdf_path, "rb").read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename="{pdf_path}"')
    msg.attach(part)
    
    server = SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(GMAIL_USER, GMAIL_APP_PASS)
    server.sendmail(GMAIL_USER, OFFICE_EMAIL, msg.as_string())
    server.quit()
    
    bot.send_message(chat_id, " සාර්ථකයි! පිරවූ PDF එක ඔබේ Office Email එකට auto-send කරන ලදී.")

bot.polling()
