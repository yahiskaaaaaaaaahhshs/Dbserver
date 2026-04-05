from flask import Flask, request, jsonify
import random
import time
import os
import json
from datetime import datetime
import re

app = Flask(__name__)

API_KEY = "yashikaaa"

def normalize_card(card_data):
    try:
        parts = card_data.split('|')
        if len(parts) != 4:
            return None
        if not re.match(r'^\d{13,16}$', parts[0]):
            return None
        if not re.match(r'^(0[1-9]|1[0-2])$', parts[1]):
            return None
        year = parts[2]
        if len(year) == 2:
            year = f"20{year}" if int(year) < 50 else f"19{year}"
        elif len(year) != 4:
            return None
        if not re.match(r'^\d{3,4}$', parts[3]):
            return None
        return f"{parts[0]}|{parts[1]}|{year}|{parts[3]}"
    except:
        return None

def load_db(filename):
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_db(filename, data):
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    except:
        pass

# ============ CHAOS AUTH (2 sec, 30% approve) ============
CHAOS_DECLINE = [
    {"response": "Issuer declined card addition", "status": "declined"},
    {"response": "Invalid card number", "status": "declined"},
    {"response": "Card expired", "status": "declined"},
    {"response": "Invalid security code", "status": "declined"},
    {"response": "Card not supported", "status": "declined"}
]

CHAOS_APPROVE = [
    {"response": "Card added successfully", "status": "approved"},
    {"response": "Payment method saved", "status": "approved"}
]

@app.route('/chaos/key=<key>/cc=<card_data>')
def chaos_auth(key, card_data):
    if key != API_KEY:
        return jsonify({"error": "Invalid API key"}), 401
    
    normalized_card = normalize_card(card_data)
    if not normalized_card:
        return jsonify({"error": "Invalid card format"}), 400
    
    db = load_db("chaos_responses.json")
    
    if normalized_card in db:
        response = db[normalized_card]
    else:
        if random.random() <= 0.3:
            response = random.choice(CHAOS_APPROVE)
        else:
            response = random.choice(CHAOS_DECLINE)
        db[normalized_card] = response
        save_db("chaos_responses.json", db)
    
    time.sleep(2)
    return jsonify({
        "card": normalized_card,
        "response": response["response"],
        "status": response["status"],
        "gateway": "Chaos Auth"
    })

# ============ ADYEN AUTH (3 sec, 20% approve) ============
ADYEN_DECLINE = [
    {"response": "Refused by issuer", "status": "declined"},
    {"response": "Invalid card details", "status": "declined"},
    {"response": "Expired card", "status": "declined"},
    {"response": "Card not supported", "status": "declined"},
    {"response": "Invalid CVV", "status": "declined"}
]

ADYEN_APPROVE = [
    {"response": "Card added to wallet", "status": "approved"},
    {"response": "Payment method saved", "status": "approved"}
]

@app.route('/adyen/key=<key>/cc=<card_data>')
def adyen_auth(key, card_data):
    if key != API_KEY:
        return jsonify({"error": "Invalid API key"}), 401
    
    normalized_card = normalize_card(card_data)
    if not normalized_card:
        return jsonify({"error": "Invalid card format"}), 400
    
    db = load_db("adyen_responses.json")
    
    if normalized_card in db:
        response = db[normalized_card]
    else:
        if random.random() <= 0.2:
            response = random.choice(ADYEN_APPROVE)
        else:
            response = random.choice(ADYEN_DECLINE)
        db[normalized_card] = response
        save_db("adyen_responses.json", db)
    
    time.sleep(3)
    return jsonify({
        "card": normalized_card,
        "response": response["response"],
        "status": response["status"],
        "gateway": "Adyen Auth"
    })

# ============ APP BASED AUTH (3 sec, 20% approve) ============
APP_DECLINE = [
    {"response": "Unable to verify card", "status": "declined"},
    {"response": "Digital wallet enrollment failed", "status": "declined"},
    {"response": "Device not recognized", "status": "declined"},
    {"response": "Biometric verification failed", "status": "declined"},
    {"response": "Tokenization failed", "status": "declined"}
]

APP_APPROVE = [
    {"response": "Card added to digital wallet", "status": "approved"},
    {"response": "Card tokenization successful", "status": "approved"}
]

@app.route('/app/key=<key>/cc=<card_data>')
def app_auth(key, card_data):
    if key != API_KEY:
        return jsonify({"error": "Invalid API key"}), 401
    
    normalized_card = normalize_card(card_data)
    if not normalized_card:
        return jsonify({"error": "Invalid card format"}), 400
    
    db = load_db("app_responses.json")
    
    if normalized_card in db:
        response = db[normalized_card]
    else:
        if random.random() <= 0.2:
            response = random.choice(APP_APPROVE)
        else:
            response = random.choice(APP_DECLINE)
        db[normalized_card] = response
        save_db("app_responses.json", db)
    
    time.sleep(3)
    return jsonify({
        "card": normalized_card,
        "response": response["response"],
        "status": response["status"],
        "gateway": "App Based Auth"
    })

# ============ AUTH NET (0.1-0.5 sec, 75% approve) ============
AUTHNET_DECLINE = [
    {"response": "The payment gateway has declined the request.", "status": "declined"},
    {"response": "The request was declined.", "status": "declined"},
    {"response": "The billing address does not match the card on file.", "status": "declined"},
    {"response": "The Card Code (CVV) is invalid.", "status": "declined"},
    {"response": "The credit card has been declined by the issuing bank.", "status": "declined"}
]

AUTHNET_APPROVE = [
    {"response": "Card added successfully", "status": "approved"},
    {"response": "Card verified and added", "status": "approved"}
]

@app.route('/authnet/key=<key>/cc=<card_data>')
def authnet(key, card_data):
    if key != API_KEY:
        return jsonify({"error": "Invalid API key"}), 401
    
    normalized_card = normalize_card(card_data)
    if not normalized_card:
        return jsonify({"error": "Invalid card format"}), 400
    
    db = load_db("authnet_responses.json")
    
    if normalized_card in db:
        response = db[normalized_card]
    else:
        if random.random() <= 0.75:
            response = random.choice(AUTHNET_APPROVE)
        else:
            response = random.choice(AUTHNET_DECLINE)
        db[normalized_card] = response
        save_db("authnet_responses.json", db)
    
    time.sleep(random.uniform(0.1, 0.5))
    return jsonify({
        "card": normalized_card,
        "response": response["response"],
        "status": response["status"],
        "gateway": "Auth Net"
    })

# ============ PAYPAL (4 sec, 20% approve) ============
PAYPAL_DECLINE = [
    {"response": "Unable to add card to PayPal", "status": "declined"},
    {"response": "Card verification failed", "status": "declined"},
    {"response": "Issuer declined card addition", "status": "declined"},
    {"response": "Card already linked to another account", "status": "declined"},
    {"response": "Invalid security code", "status": "declined"}
]

PAYPAL_APPROVE = [
    {"response": "Card added to PayPal successfully", "status": "approved"},
    {"response": "Card verified and linked to PayPal", "status": "approved"}
]

@app.route('/paypal/key=<key>/cc=<card_data>')
def paypal(key, card_data):
    if key != API_KEY:
        return jsonify({"error": "Invalid API key"}), 401
    
    normalized_card = normalize_card(card_data)
    if not normalized_card:
        return jsonify({"error": "Invalid card format"}), 400
    
    db = load_db("paypal_responses.json")
    
    if normalized_card in db:
        response = db[normalized_card]
    else:
        if random.random() <= 0.2:
            response = random.choice(PAYPAL_APPROVE)
        else:
            response = random.choice(PAYPAL_DECLINE)
        db[normalized_card] = response
        save_db("paypal_responses.json", db)
    
    time.sleep(4)
    return jsonify({
        "card": normalized_card,
        "response": response["response"],
        "status": response["status"],
        "gateway": "PayPal"
    })

# ============ ROOT ENDPOINT ============
@app.route('/')
def home():
    return jsonify({
        "message": "Payment Gateway APIs are running!",
        "gateways": {
            "chaos": "/chaos/key=yashikaaa/cc=CC|MM|YY|CVV",
            "adyen": "/adyen/key=yashikaaa/cc=CC|MM|YY|CVV",
            "app": "/app/key=yashikaaa/cc=CC|MM|YY|CVV",
            "authnet": "/authnet/key=yashikaaa/cc=CC|MM|YY|CVV",
            "paypal": "/paypal/key=yashikaaa/cc=CC|MM|YY|CVV"
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
