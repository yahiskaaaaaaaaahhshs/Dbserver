from flask import Flask, request, jsonify
import random
import time
import os
import json
from datetime import datetime
import re
import threading
from werkzeug.serving import make_server

API_KEY = "yashikaaa"
CARD_FORMAT = r'^\d{13,16}\|\d{2}\|\d{2,4}\|\d{3,4}$'

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

def log_transaction(log_file, card_data, response):
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, 'a') as f:
            f.write(f"{timestamp}|{card_data}|{json.dumps(response)}\n")
    except:
        pass

# ==============================================
# Chaos Auth - Port 5000 (2 sec delay, 30% approve)
# ==============================================
def create_chaos_auth():
    app = Flask("Chaos_Auth")
    RESPONSE_DB_FILE = "chaos_responses.json"
    LOG_FILE = "chaos_transactions.log"
    
    DECLINE_RESPONSES = [
        {"response": "Issuer declined card addition", "status": "declined"},
        {"response": "Invalid card number", "status": "declined"},
        {"response": "Card expired", "status": "declined"},
        {"response": "Invalid security code", "status": "declined"},
        {"response": "Card not supported", "status": "declined"},
        {"response": "Card already exists", "status": "declined"},
        {"response": "Billing address mismatch", "status": "declined"},
        {"response": "Card restricted by issuer", "status": "declined"},
        {"response": "Unable to verify card", "status": "declined"},
        {"response": "Issuer unavailable", "status": "declined"}
    ]
    
    APPROVE_RESPONSES = [
        {"response": "Card added successfully", "status": "approved"},
        {"response": "Payment method saved", "status": "approved"},
        {"response": "Card verified and added", "status": "approved"},
        {"response": "Card successfully linked", "status": "approved"}
    ]

    @app.route('/key=<key>/cc=<card_data>')
    def process(key, card_data):
        if key != API_KEY:
            return jsonify({"error": "Invalid API key"}), 401
        
        normalized_card = normalize_card(card_data)
        if not normalized_card:
            return jsonify({"error": "Invalid card format. Use CC|MM|YY|CVV or CC|MM|YYYY|CVV"}), 400
        
        db = load_db(RESPONSE_DB_FILE)
        
        if normalized_card in db:
            response = db[normalized_card]
        else:
            if random.random() <= 0.3:
                response = random.choice(APPROVE_RESPONSES)
            else:
                response = random.choice(DECLINE_RESPONSES)
            
            db[normalized_card] = response
            save_db(RESPONSE_DB_FILE, db)
        
        time.sleep(2)
        log_transaction(LOG_FILE, normalized_card, response)
        
        return jsonify({
            "card": normalized_card,
            "response": response["response"],
            "status": response["status"],
            "gateway": "Chaos Auth"
        })
    
    return app

# ==============================================
# Adyen Auth - Port 3600 (3 sec delay, 20% approve)
# ==============================================
def create_adyen_auth():
    app = Flask("Adyen_Auth")
    RESPONSE_DB_FILE = "adyen_responses.json"
    LOG_FILE = "adyen_transactions.log"
    
    DECLINE_RESPONSES = [
        {"response": "Refused by issuer", "status": "declined"},
        {"response": "Invalid card details", "status": "declined"},
        {"response": "Expired card", "status": "declined"},
        {"response": "Card not supported", "status": "declined"},
        {"response": "Restricted card", "status": "declined"},
        {"response": "Invalid CVV", "status": "declined"},
        {"response": "Card already added", "status": "declined"},
        {"response": "Issuer timeout", "status": "declined"},
        {"response": "3D Secure failed", "status": "declined"},
        {"response": "Account verification needed", "status": "declined"}
    ]
    
    APPROVE_RESPONSES = [
        {"response": "Card added to wallet", "status": "approved"},
        {"response": "Payment method saved", "status": "approved"},
        {"response": "Card verified and stored", "status": "approved"},
        {"response": "Card successfully linked", "status": "approved"}
    ]

    @app.route('/key=<key>/cc=<card_data>')
    def process(key, card_data):
        if key != API_KEY:
            return jsonify({"error": "Invalid API key"}), 401
        
        normalized_card = normalize_card(card_data)
        if not normalized_card:
            return jsonify({"error": "Invalid card format. Use CC|MM|YY|CVV or CC|MM|YYYY|CVV"}), 400
        
        db = load_db(RESPONSE_DB_FILE)
        
        if normalized_card in db:
            response = db[normalized_card]
        else:
            if random.random() <= 0.2:
                response = random.choice(APPROVE_RESPONSES)
            else:
                response = random.choice(DECLINE_RESPONSES)
            
            db[normalized_card] = response
            save_db(RESPONSE_DB_FILE, db)
        
        time.sleep(3)
        log_transaction(LOG_FILE, normalized_card, response)
        
        return jsonify({
            "card": normalized_card,
            "response": response["response"],
            "status": response["status"],
            "gateway": "Adyen Auth"
        })
    
    return app

# ==============================================
# App Based Auth - Port 7000 (3 sec delay, 20% approve)
# ==============================================
def create_app_auth():
    app = Flask("App_Auth")
    RESPONSE_DB_FILE = "app_responses.json"
    LOG_FILE = "app_transactions.log"
    
    DECLINE_RESPONSES = [
        {"response": "Unable to verify card", "status": "declined"},
        {"response": "Digital wallet enrollment failed", "status": "declined"},
        {"response": "Issuer not supporting digital cards", "status": "declined"},
        {"response": "Device not recognized", "status": "declined"},
        {"response": "Biometric verification failed", "status": "declined"},
        {"response": "Tokenization failed", "status": "declined"},
        {"response": "Card already in wallet", "status": "declined"},
        {"response": "Secure element error", "status": "declined"},
        {"response": "Invalid card details", "status": "declined"},
        {"response": "Card expired", "status": "declined"}
    ]
    
    APPROVE_RESPONSES = [
        {"response": "Card added to digital wallet", "status": "approved"},
        {"response": "Payment method saved in app", "status": "approved"},
        {"response": "Card tokenization successful", "status": "approved"},
        {"response": "Digital card issued", "status": "approved"}
    ]

    @app.route('/key=<key>/cc=<card_data>')
    def process(key, card_data):
        if key != API_KEY:
            return jsonify({"error": "Invalid API key"}), 401
        
        normalized_card = normalize_card(card_data)
        if not normalized_card:
            return jsonify({"error": "Invalid card format. Use CC|MM|YY|CVV or CC|MM|YYYY|CVV"}), 400
        
        db = load_db(RESPONSE_DB_FILE)
        
        if normalized_card in db:
            response = db[normalized_card]
        else:
            if random.random() <= 0.2:
                response = random.choice(APPROVE_RESPONSES)
            else:
                response = random.choice(DECLINE_RESPONSES)
            
            db[normalized_card] = response
            save_db(RESPONSE_DB_FILE, db)
        
        time.sleep(3)
        log_transaction(LOG_FILE, normalized_card, response)
        
        return jsonify({
            "card": normalized_card,
            "response": response["response"],
            "status": response["status"],
            "gateway": "App Based Auth"
        })
    
    return app

# ==============================================
# Auth Net - Port 6000 (0.1-0.5 sec, 75% approve)
# ==============================================
def create_authnet():
    app = Flask("Auth_Net")
    RESPONSE_DB_FILE = "authnet_responses.json"
    LOG_FILE = "authnet_transactions.log"
    
    DECLINE_RESPONSES = [
        {"response": "The payment gateway has declined the request.", "status": "declined"},
        {"response": "The request was declined.", "status": "declined"},
        {"response": "The billing address does not match the card on file.", "status": "declined"},
        {"response": "The Card Code (CVV) is invalid.", "status": "declined"},
        {"response": "The credit card has been declined by the issuing bank.", "status": "declined"}
    ]
    
    APPROVE_RESPONSES = [
        {"response": "Card added successfully", "status": "approved"},
        {"response": "Payment method saved", "status": "approved"},
        {"response": "Card verified and added", "status": "approved"},
        {"response": "Card successfully linked to account", "status": "approved"}
    ]

    @app.route('/key=<key>/cc=<card_data>')
    def process(key, card_data):
        if key != API_KEY:
            return jsonify({"error": "Invalid API key"}), 401
        
        normalized_card = normalize_card(card_data)
        if not normalized_card:
            return jsonify({"error": "Invalid card format. Use CC|MM|YY|CVV or CC|MM|YYYY|CVV"}), 400
        
        db = load_db(RESPONSE_DB_FILE)
        
        if normalized_card in db:
            response = db[normalized_card]
        else:
            if random.random() <= 0.75:
                response = random.choice(APPROVE_RESPONSES)
            else:
                response = random.choice(DECLINE_RESPONSES)
            
            db[normalized_card] = response
            save_db(RESPONSE_DB_FILE, db)
        
        time.sleep(random.uniform(0.1, 0.5))
        log_transaction(LOG_FILE, normalized_card, response)
        
        return jsonify({
            "card": normalized_card,
            "response": response["response"],
            "status": response["status"],
            "gateway": "Auth Net"
        })
    
    return app

# ==============================================
# PayPal - Port 8000 (4 sec delay, 20% approve)
# ==============================================
def create_paypal():
    app = Flask("PayPal")
    RESPONSE_DB_FILE = "paypal_responses.json"
    LOG_FILE = "paypal_transactions.log"
    
    DECLINE_RESPONSES = [
        {"response": "Unable to add card to PayPal", "status": "declined"},
        {"response": "Card verification failed", "status": "declined"},
        {"response": "Issuer declined card addition", "status": "declined"},
        {"response": "Card already linked to another account", "status": "declined"},
        {"response": "Invalid security code", "status": "declined"},
        {"response": "Card expired", "status": "declined"},
        {"response": "Card type not accepted", "status": "declined"},
        {"response": "Billing address mismatch", "status": "declined"},
        {"response": "PayPal account restricted", "status": "declined"},
        {"response": "Tokenization failed", "status": "declined"}
    ]
    
    APPROVE_RESPONSES = [
        {"response": "Card added to PayPal successfully", "status": "approved"},
        {"response": "Payment method saved in PayPal", "status": "approved"},
        {"response": "Card verified and linked to PayPal", "status": "approved"},
        {"response": "New card added to your PayPal wallet", "status": "approved"}
    ]

    @app.route('/key=<key>/cc=<card_data>')
    def process(key, card_data):
        if key != API_KEY:
            return jsonify({"error": "Invalid API key"}), 401
        
        normalized_card = normalize_card(card_data)
        if not normalized_card:
            return jsonify({"error": "Invalid card format. Use CC|MM|YY|CVV or CC|MM|YYYY|CVV"}), 400
        
        db = load_db(RESPONSE_DB_FILE)
        
        if normalized_card in db:
            response = db[normalized_card]
        else:
            if random.random() <= 0.2:
                response = random.choice(APPROVE_RESPONSES)
            else:
                response = random.choice(DECLINE_RESPONSES)
            
            db[normalized_card] = response
            save_db(RESPONSE_DB_FILE, db)
        
        time.sleep(4)
        log_transaction(LOG_FILE, normalized_card, response)
        
        return jsonify({
            "card": normalized_card,
            "response": response["response"],
            "status": response["status"],
            "gateway": "PayPal"
        })
    
    return app

# ==============================================
# Start all servers
# ==============================================
def run_servers():
    servers = [
        make_server('0.0.0.0', 5000, create_chaos_auth()),
        make_server('0.0.0.0', 3600, create_adyen_auth()),
        make_server('0.0.0.0', 7000, create_app_auth()),
        make_server('0.0.0.0', 6000, create_authnet()),
        make_server('0.0.0.0', 8000, create_paypal())
    ]
    
    threads = []
    for server in servers:
        t = threading.Thread(target=server.serve_forever)
        threads.append(t)
        t.start()
    
    print("=" * 50)
    print("All payment gateway APIs are running (CARD ADD MODE)")
    print("=" * 50)
    print("Chaos Auth    | Port 5000 | 2 sec delay | 30% approve")
    print("Adyen Auth    | Port 3600 | 3 sec delay | 20% approve")
    print("App Based Auth| Port 7000 | 3 sec delay | 20% approve")
    print("Auth Net      | Port 6000 | 0.1-0.5 sec | 75% approve")
    print("PayPal        | Port 8000 | 4 sec delay | 20% approve")
    print("=" * 50)
    print("\nExample URL:")
    print("http://localhost:5000/key=yashikaaa/cc=4111111111111111|12|25|123")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        for server in servers:
            server.shutdown()
        for t in threads:
            t.join()

if __name__ == '__main__':
    run_servers()
