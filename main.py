from flask import Flask, request, jsonify
import random
import time
import os
import json
from datetime import datetime
import re
import threading
import sys

# Common configuration
API_KEY = "yashikaaa"
CARD_FORMAT = r'^\d{13,16}\|\d{2}\|\d{2,4}\|\d{3,4}$'

# Railway provides the PORT environment variable
PORT = int(os.environ.get('PORT', 5000))

def normalize_card(card_data):
    """Normalize card format to CC|MM|YYYY|CVV and validate"""
    try:
        parts = card_data.split('|')
        if len(parts) != 4:
            return None
        
        # Validate card number (13-16 digits)
        if not re.match(r'^\d{13,16}$', parts[0]):
            return None
            
        # Validate month (01-12)
        if not re.match(r'^(0[1-9]|1[0-2])$', parts[1]):
            return None
            
        # Normalize year (accept YY or YYYY)
        year = parts[2]
        if len(year) == 2:  # Convert YY to YYYY
            year = f"20{year}" if int(year) < 50 else f"19{year}"
        elif len(year) != 4:
            return None
            
        # Validate CVV (3-4 digits)
        if not re.match(r'^\d{3,4}$', parts[3]):
            return None
            
        return f"{parts[0]}|{parts[1]}|{year}|{parts[3]}"
    except:
        return None

def load_db(filename):
    """Load response database from file"""
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_db(filename, data):
    """Save response database to file"""
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    except:
        pass

def load_database(filename):
    """Load existing responses from JSON file for charge APIs"""
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"transactions": []}

def save_database(data, filename):
    """Save responses to JSON file"""
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    except IOError:
        pass

def log_transaction(log_file, card_data, response):
    """Log transaction with timestamp"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, 'a') as f:
            f.write(f"{timestamp}|{card_data}|{json.dumps(response)}\n")
    except:
        pass

def random_delay():
    """Generate random delay between 15-35 seconds"""
    return random.randint(15, 35)

# ==============================================
# Main Flask App with multiple routes
# ==============================================
app = Flask(__name__)

# ==============================================
# Chaos Auth - 7 second delay
# ==============================================
CHAOS_RESPONSE_DB_FILE = "chaos_responses.json"
CHAOS_LOG_FILE = "chaos_transactions.log"

CHAOS_DECLINE_RESPONSES = [
    {"response": "Processor decline - Contact issuer", "status": "declined"},
    {"response": "Invalid security code", "status": "declined"},
    {"response": "Expired payment method", "status": "declined"},
    {"response": "Insufficient funds", "status": "declined"},
    {"response": "Transaction not permitted", "status": "declined"},
    {"response": "Card restricted by issuer", "status": "declined"},
    {"response": "Invalid transaction", "status": "declined"},
    {"response": "Lost card", "status": "declined"},
    {"response": "Stolen card", "status": "declined"},
    {"response": "Exceeds withdrawal limit", "status": "declined"},
    {"response": "Invalid account", "status": "declined"},
    {"response": "System malfunction", "status": "declined"},
    {"response": "Card not supported", "status": "declined"},
    {"response": "Suspected fraud", "status": "declined"},
    {"response": "3D Secure authentication failed", "status": "declined"},
    {"response": "Issuer unavailable", "status": "declined"},
    {"response": "Duplicate transaction", "status": "declined"},
    {"response": "Invalid amount", "status": "declined"},
    {"response": "Payment method not accepted", "status": "declined"},
    {"response": "Authorization failed", "status": "declined"}
]

CHAOS_APPROVE_RESPONSES = [
    {"response": "Payment authorized", "status": "approved"},
    {"response": "Charge successful", "status": "approved"},
    {"response": "Transaction completed", "status": "approved"},
    {"response": "Funds transferred", "status": "approved"},
    {"response": "Payment processed", "status": "approved"}
]

@app.route('/chaos/key=<key>/cc=<card_data>')
def chaos_process(key, card_data):
    if key != API_KEY:
        return jsonify({"error": "Invalid API key"}), 401
    
    normalized_card = normalize_card(card_data)
    if not normalized_card:
        return jsonify({"error": "Invalid card format. Use CC|MM|YY|CVV or CC|MM|YYYY|CVV"}), 400
    
    # Load database
    db = load_db(CHAOS_RESPONSE_DB_FILE)
    
    # Check for existing response
    if normalized_card in db:
        response = db[normalized_card]
    else:
        # 30% approval chance
        if random.random() <= 0.3:
            response = random.choice(CHAOS_APPROVE_RESPONSES)
        else:
            response = random.choice(CHAOS_DECLINE_RESPONSES)
        
        # Save new response
        db[normalized_card] = response
        save_db(CHAOS_RESPONSE_DB_FILE, db)
    
    # Processing delay
    time.sleep(7)
    
    # Log transaction
    log_transaction(CHAOS_LOG_FILE, normalized_card, response)
    
    return jsonify({
        "card": normalized_card,
        "response": response["response"],
        "status": response["status"],
        "gateway": "Chaos Auth"
    })

# ==============================================
# Adyen Auth - 16 second delay
# ==============================================
ADYEN_RESPONSE_DB_FILE = "adyen_responses.json"
ADYEN_LOG_FILE = "adyen_transactions.log"

ADYEN_DECLINE_RESPONSES = [
    {"response": "3D Secure authentication required", "status": "declined"},
    {"response": "SCA challenge failed", "status": "declined"},
    {"response": "Issuer declined", "status": "declined"},
    {"response": "Risk check failed", "status": "declined"},
    {"response": "Payment method not supported", "status": "declined"},
    {"response": "Technical error", "status": "declined"},
    {"response": "Refused by issuer", "status": "declined"},
    {"response": "Invalid card details", "status": "declined"},
    {"response": "Expired card", "status": "declined"},
    {"response": "Currency not supported", "status": "declined"},
    {"response": "Limit exceeded", "status": "declined"},
    {"response": "Merchant mismatch", "status": "declined"},
    {"response": "Account verification needed", "status": "declined"},
    {"response": "Recurring not enabled", "status": "declined"},
    {"response": "AVS check failed", "status": "declined"},
    {"response": "CVC check failed", "status": "declined"},
    {"response": "Chargeback protection", "status": "declined"},
    {"response": "Country not supported", "status": "declined"},
    {"response": "Processing error", "status": "declined"},
    {"response": "Payment provider rejected", "status": "declined"}
]

ADYEN_APPROVE_RESPONSES = [
    {"response": "Adyen payment authorized", "status": "approved"},
    {"response": "SCA verification passed", "status": "approved"},
    {"response": "Payment captured", "status": "approved"},
    {"response": "Transaction settled", "status": "approved"},
    {"response": "Funds reserved", "status": "approved"}
]

@app.route('/adyen/key=<key>/cc=<card_data>')
def adyen_process(key, card_data):
    if key != API_KEY:
        return jsonify({"error": "Invalid API key"}), 401
    
    normalized_card = normalize_card(card_data)
    if not normalized_card:
        return jsonify({"error": "Invalid card format. Use CC|MM|YY|CVV or CC|MM|YYYY|CVV"}), 400
    
    db = load_db(ADYEN_RESPONSE_DB_FILE)
    
    if normalized_card in db:
        response = db[normalized_card]
    else:
        # 20% approval chance
        if random.random() <= 0.2:
            response = random.choice(ADYEN_APPROVE_RESPONSES)
        else:
            response = random.choice(ADYEN_DECLINE_RESPONSES)
        
        db[normalized_card] = response
        save_db(ADYEN_RESPONSE_DB_FILE, db)
    
    time.sleep(3)
    log_transaction(ADYEN_LOG_FILE, normalized_card, response)
    return jsonify({
        "card": normalized_card,
        "response": response["response"],
        "status": response["status"],
        "gateway": "Adyen Auth"
    })

# ==============================================
# App Based Auth - 27 second delay
# ==============================================
APP_RESPONSE_DB_FILE = "app_responses.json"
APP_LOG_FILE = "app_transactions.log"

APP_DECLINE_RESPONSES = [
    {"response": "Unable to verify card", "status": "declined"},
    {"response": "Mobile payment verification failed", "status": "declined"},
    {"response": "Issuer not supporting digital wallets", "status": "declined"},
    {"response": "Device not recognized", "status": "declined"},
    {"response": "Biometric verification failed", "status": "declined"},
    {"response": "App version outdated", "status": "declined"},
    {"response": "Tokenization error", "status": "declined"},
    {"response": "Digital wallet limit reached", "status": "declined"},
    {"response": "Device rooted/jailbroken", "status": "declined"},
    {"response": "App not authorized", "status": "declined"},
    {"response": "Session expired", "status": "declined"},
    {"response": "Location mismatch", "status": "declined"},
    {"response": "Device timeout", "status": "declined"},
    {"response": "Network error", "status": "declined"},
    {"response": "Invalid token", "status": "declined"},
    {"response": "Too many attempts", "status": "declined"},
    {"response": "App not verified", "status": "declined"},
    {"response": "Card already exists", "status": "declined"},
    {"response": "Secure element error", "status": "declined"},
    {"response": "Digital card expired", "status": "declined"}
]

APP_APPROVE_RESPONSES = [
    {"response": "Card successfully added", "status": "approved"},
    {"response": "Payment method saved to wallet", "status": "approved"},
    {"response": "Tokenization successful", "status": "approved"},
    {"response": "Digital card issued", "status": "approved"},
    {"response": "Biometric verification passed", "status": "approved"}
]

@app.route('/app-auth/key=<key>/cc=<card_data>')
def app_auth_process(key, card_data):
    if key != API_KEY:
        return jsonify({"error": "Invalid API key"}), 401
    
    normalized_card = normalize_card(card_data)
    if not normalized_card:
        return jsonify({"error": "Invalid card format. Use CC|MM|YY|CVV or CC|MM|YYYY|CVV"}), 400
    
    db = load_db(APP_RESPONSE_DB_FILE)
    
    if normalized_card in db:
        response = db[normalized_card]
    else:
        # 28.5% approval chance
        if random.randint(1, 25) <= 5:
            response = random.choice(APP_APPROVE_RESPONSES)
        else:
            response = random.choice(APP_DECLINE_RESPONSES)
        
        db[normalized_card] = response
        save_db(APP_RESPONSE_DB_FILE, db)
    
    time.sleep(27)
    log_transaction(APP_LOG_FILE, normalized_card, response)
    return jsonify({
        "card": normalized_card,
        "response": response["response"],
        "status": response["status"],
        "gateway": "App Based Auth"
    })

# ==============================================
# Payflow - 30-45 second delay
# ==============================================
PAYFLOW_RESPONSE_DB_FILE = "payflow_responses.json"
PAYFLOW_LOG_FILE = "payflow_transactions.log"

PAYFLOW_DECLINE_RESPONSES = [
    {"response": "Insufficient funds", "status": "declined"},
    {"response": "Invalid security code", "status": "declined"},
    {"response": "Payment rejected", "status": "declined"},
    {"response": "Bank declined transaction", "status": "declined"},
    {"response": "Card not active", "status": "declined"},
    {"response": "Invalid expiration date", "status": "declined"},
    {"response": "Transaction timeout", "status": "declined"},
    {"response": "Processor declined", "status": "declined"},
    {"response": "Billing address mismatch", "status": "declined"},
    {"response": "Card type not accepted", "status": "declined"},
    {"response": "Maximum payment attempts", "status": "declined"},
    {"response": "Risk threshold exceeded", "status": "declined"},
    {"response": "Payment configuration error", "status": "declined"},
    {"response": "Currency conversion failed", "status": "declined"},
    {"response": "Account verification needed", "status": "declined"},
    {"response": "Payment gateway error", "status": "declined"},
    {"response": "Transaction canceled", "status": "declined"},
    {"response": "Invalid merchant ID", "status": "declined"},
    {"response": "Payment method restricted", "status": "declined"},
    {"response": "Authorization expired", "status": "declined"}
]

PAYFLOW_APPROVE_RESPONSES = [
    {"response": "Payment successful", "status": "approved"},
    {"response": "Payment captured", "status": "approved"},
    {"response": "Funds transferred", "status": "approved"},
    {"response": "Transaction completed", "status": "approved"},
    {"response": "Authorization approved", "status": "approved"}
]

@app.route('/payflow/key=<key>/cc=<card_data>')
def payflow_process(key, card_data):
    if key != API_KEY:
        return jsonify({"error": "Invalid API key"}), 401
    
    normalized_card = normalize_card(card_data)
    if not normalized_card:
        return jsonify({"error": "Invalid card format. Use CC|MM|YY|CVV or CC|MM|YYYY|CVV"}), 400
    
    db = load_db(PAYFLOW_RESPONSE_DB_FILE)
    
    if normalized_card in db:
        response = db[normalized_card]
    else:
        # 20% approval chance
        if random.randint(1, 25) <= 5:
            response = random.choice(PAYFLOW_APPROVE_RESPONSES)
        else:
            response = random.choice(PAYFLOW_DECLINE_RESPONSES)
        
        db[normalized_card] = response
        save_db(PAYFLOW_RESPONSE_DB_FILE, db)
    
    # Random delay between 30-45 seconds
    time.sleep(random.randint(30, 45))
    log_transaction(PAYFLOW_LOG_FILE, normalized_card, response)
    return jsonify({
        "card": normalized_card,
        "response": response["response"],
        "status": response["status"],
        "gateway": "Payflow"
    })

# ==============================================
# Random Auth - 7 second delay
# ==============================================
RANDOM_RESPONSE_DB_FILE = "random_responses.json"
RANDOM_LOG_FILE = "random_transactions.log"

RANDOM_ALL_RESPONSES = [
    {"response": "3D Secure required", "status": "auth_required"},
    {"response": "Insufficient funds", "status": "declined"},
    {"response": "Invalid security code", "status": "declined"},
    {"response": "Payment processed", "status": "approved"},
    {"response": "Authorization successful", "status": "approved"},
    {"response": "Card restricted", "status": "declined"},
    {"response": "Account frozen", "status": "declined"},
    {"response": "Daily limit exceeded", "status": "declined"},
    {"response": "Payment pending", "status": "pending"},
    {"response": "Charge successful", "status": "approved"},
    {"response": "Issuer not available", "status": "declined"},
    {"response": "Invalid transaction type", "status": "declined"},
    {"response": "Manual review required", "status": "pending"},
    {"response": "Payment approved", "status": "approved"},
    {"response": "Card not supported", "status": "declined"},
    {"response": "Bank connection error", "status": "declined"},
    {"response": "Transaction completed", "status": "approved"},
    {"response": "Fraud check failed", "status": "declined"},
    {"response": "Payment method blocked", "status": "declined"},
    {"response": "System error", "status": "declined"},
    {"response": "Authorization failed", "status": "declined"},
    {"response": "CVV verification needed", "status": "auth_required"},
    {"response": "Payment reversed", "status": "declined"},
    {"response": "Account not found", "status": "declined"},
    {"response": "Transaction approved", "status": "approved"}
]

@app.route('/random/key=<key>/cc=<card_data>')
def random_auth_process(key, card_data):
    if key != API_KEY:
        return jsonify({"error": "Invalid API key"}), 401
    
    normalized_card = normalize_card(card_data)
    if not normalized_card:
        return jsonify({"error": "Invalid card format. Use CC|MM|YY|CVV or CC|MM|YYYY|CVV"}), 400
    
    db = load_db(RANDOM_RESPONSE_DB_FILE)
    
    if normalized_card in db:
        response = db[normalized_card]
    else:
        response = random.choice(RANDOM_ALL_RESPONSES)
        db[normalized_card] = response
        save_db(RANDOM_RESPONSE_DB_FILE, db)
    
    time.sleep(7)
    log_transaction(RANDOM_LOG_FILE, normalized_card, response)
    return jsonify({
        "card": normalized_card,
        "response": response["response"],
        "status": response["status"],
        "gateway": "Random Auth"
    })

# ==============================================
# Shopify - 20-45 second delay
# ==============================================
SHOPIFY_RESPONSE_DB_FILE = "shopify_responses.json"
SHOPIFY_LOG_FILE = "shopify_transactions.log"

SHOPIFY_DECLINE_RESPONSES = [
    {"response": "Shopify fraud check failed", "status": "declined"},
    {"response": "High risk order", "status": "declined"},
    {"response": "Billing address mismatch", "status": "declined"},
    {"response": "AVS verification failed", "status": "declined"},
    {"response": "Unverified customer", "status": "declined"},
    {"response": "Order flagged for review", "status": "declined"},
    {"response": "IP address mismatch", "status": "declined"},
    {"response": "Shipping restriction", "status": "declined"},
    {"response": "Product restriction", "status": "declined"},
    {"response": "Quantity limit exceeded", "status": "declined"},
    {"response": "New customer restriction", "status": "declined"},
    {"response": "Velocity check failed", "status": "declined"},
    {"response": "Proxy/VPN detected", "status": "declined"},
    {"response": "Country restriction", "status": "declined"},
    {"response": "Payment gateway timeout", "status": "declined"},
    {"response": "Shopify Payments error", "status": "declined"},
    {"response": "Duplicate order detected", "status": "declined"},
    {"response": "Risk analysis failed", "status": "declined"},
    {"response": "Payment provider error", "status": "declined"},
    {"response": "Checkout expired", "status": "declined"}
]

SHOPIFY_APPROVE_RESPONSES = [
    {"response": "Shopify payment processed", "status": "approved"},
    {"response": "Order marked as paid", "status": "approved"},
    {"response": "Payment captured", "status": "approved"},
    {"response": "Transaction completed", "status": "approved"},
    {"response": "Funds transferred", "status": "approved"}
]

@app.route('/shopify/key=<key>/cc=<card_data>')
def shopify_process(key, card_data):
    if key != API_KEY:
        return jsonify({"error": "Invalid API key"}), 401
    
    normalized_card = normalize_card(card_data)
    if not normalized_card:
        return jsonify({"error": "Invalid card format. Use CC|MM|YY|CVV or CC|MM|YYYY|CVV"}), 400
    
    db = load_db(SHOPIFY_RESPONSE_DB_FILE)
    
    if normalized_card in db:
        response = db[normalized_card]
    else:
        # 5% approval chance
        if random.random() <= 0.05:
            response = random.choice(SHOPIFY_APPROVE_RESPONSES)
        else:
            response = random.choice(SHOPIFY_DECLINE_RESPONSES)
        
        db[normalized_card] = response
        save_db(SHOPIFY_RESPONSE_DB_FILE, db)
    
    # Random delay between 20-45 seconds
    time.sleep(random.randint(20, 45))
    log_transaction(SHOPIFY_LOG_FILE, normalized_card, response)
    return jsonify({
        "card": normalized_card,
        "response": response["response"],
        "status": response["status"],
        "gateway": "Shopify"
    })

# ==============================================
# Skrill - 1-3 second delay
# ==============================================
SKRILL_RESPONSE_DB_FILE = "skrill_responses.json"
SKRILL_LOG_FILE = "skrill_transactions.log"

SKRILL_DECLINE_RESPONSES = [
    {"response": "Insufficient funds", "status": "declined"},
    {"response": "Payment method not supported", "status": "declined"},
    {"response": "Account not verified", "status": "declined"},
    {"response": "Country restriction", "status": "declined"},
    {"response": "Currency not accepted", "status": "declined"},
    {"response": "Daily limit reached", "status": "declined"},
    {"response": "Email not verified", "status": "declined"},
    {"response": "Exchange rate expired", "status": "declined"},
    {"response": "Invalid recipient", "status": "declined"},
    {"response": "Merchant not accepted", "status": "declined"},
    {"response": "Monthly limit exceeded", "status": "declined"},
    {"response": "New account restriction", "status": "declined"},
    {"response": "Password reset required", "status": "declined"},
    {"response": "Payment refused", "status": "declined"},
    {"response": "Phone verification needed", "status": "declined"},
    {"response": "Risk check failed", "status": "declined"},
    {"response": "Security question needed", "status": "declined"},
    {"response": "Temporary hold", "status": "declined"},
    {"response": "Transaction blocked", "status": "declined"},
    {"response": "Wallet inactive", "status": "declined"}
]

SKRILL_APPROVE_RESPONSES = [
    {"response": "Payment processed successfully", "status": "approved"},
    {"response": "Payment authorized", "status": "approved"},
    {"response": "Money transfer complete", "status": "approved"},
    {"response": "Transaction settled", "status": "approved"},
    {"response": "Funds available", "status": "approved"}
]

@app.route('/skrill/key=<key>/cc=<card_data>')
def skrill_process(key, card_data):
    if key != API_KEY:
        return jsonify({"error": "Invalid API key"}), 401
    
    normalized_card = normalize_card(card_data)
    if not normalized_card:
        return jsonify({"error": "Invalid card format. Use CC|MM|YY|CVV or CC|MM|YYYY|CVV"}), 400
    
    db = load_db(SKRILL_RESPONSE_DB_FILE)
    
    if normalized_card in db:
        response = db[normalized_card]
    else:
        # 10% approval chance
        if random.random() <= 0.1:
            response = random.choice(SKRILL_APPROVE_RESPONSES)
        else:
            response = random.choice(SKRILL_DECLINE_RESPONSES)
        
        db[normalized_card] = response
        save_db(SKRILL_RESPONSE_DB_FILE, db)
    
    # Random delay between 1-3 seconds
    time.sleep(random.uniform(1, 3))
    log_transaction(SKRILL_LOG_FILE, normalized_card, response)
    return jsonify({
        "card": normalized_card,
        "response": response["response"],
        "status": response["status"],
        "gateway": "Skrill"
    })

# ==============================================
# Braintree Donation Gateway
# ==============================================
BRAINTREE_DB_FILE = "braintree_transactions.json"

BRAINTREE_APPROVED_RESPONSES = [
    {"response": "Donation processed successfully", "status": "approved"},
    {"response": "Thank you for your donation", "status": "approved"}
]

BRAINTREE_DECLINED_RESPONSES = [
    {"response": "Donation declined - insufficient funds", "status": "declined"},
    {"response": "Non-profit donations not supported on this card", "status": "declined"},
    {"response": "Recurring donation limit reached", "status": "declined"},
    {"response": "Donation amount too high", "status": "declined"},
    {"response": "Charity verification required", "status": "declined"},
    {"response": "Donation processor unavailable", "status": "declined"},
    {"response": "International donation restrictions apply", "status": "declined"},
    {"response": "Tax receipt generation failed", "status": "declined"},
    {"response": "Donation frequency limit exceeded", "status": "declined"},
    {"response": "Anonymous donations not allowed", "status": "declined"},
    {"response": "Payment method not eligible for donations", "status": "declined"},
    {"response": "Donation amount below minimum", "status": "declined"},
    {"response": "Organization verification pending", "status": "declined"},
    {"response": "Donation processor error", "status": "declined"},
    {"response": "Temporary hold on donations", "status": "declined"}
]

braintree_db = load_database(BRAINTREE_DB_FILE)

@app.route('/braintree/key=<key>/cc=<card_data>', methods=['GET'])
def braintree_process(key, card_data):
    if key != API_KEY:
        return jsonify({"error": "Invalid authentication key"}), 401
    
    if not re.match(r'^\d{13,16}\|\d{2}\|\d{2,4}\|\d{3,4}$', card_data):
        return jsonify({"error": "Invalid card format. Use CC|MM|YY|CVV or CC|MM|YYYY|CVV"}), 400
    
    # Check if card exists in database
    existing_tx = next((tx for tx in braintree_db["transactions"] if tx["cc"] == card_data), None)
    
    if existing_tx:
        result = {"response": existing_tx["response"], "status": existing_tx["status"]}
    else:
        # 1 out of 70 chance (1.4% approval rate)
        if random.randint(1, 70) == 1:
            response_data = random.choice(BRAINTREE_APPROVED_RESPONSES)
        else:
            response_data = random.choice(BRAINTREE_DECLINED_RESPONSES)
        
        new_tx = {
            "cc": card_data,
            "response": response_data["response"],
            "status": response_data["status"],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        braintree_db["transactions"].append(new_tx)
        save_database(braintree_db, BRAINTREE_DB_FILE)
        result = {"response": response_data["response"], "status": response_data["status"]}
    
    time.sleep(random_delay())
    return jsonify({"cc": card_data, "response": result["response"], "status": result["status"]})

# ==============================================
# Stripe Site Gateway
# ==============================================
STRIPE_DB_FILE = "stripe_transactions.json"

STRIPE_APPROVED_RESPONSES = [
    {"response": "Payment processed by Stripe", "status": "approved"},
    {"response": "Stripe charge successful", "status": "approved"}
]

STRIPE_DECLINED_RESPONSES = [
    {"response": "Stripe authentication failed", "status": "declined"},
    {"response": "3D Secure verification required", "status": "declined"},
    {"response": "Stripe radar blocked transaction", "status": "declined"},
    {"response": "Stripe API limit exceeded", "status": "declined"},
    {"response": "Currency not supported by Stripe", "status": "declined"},
    {"response": "Stripe account restricted", "status": "declined"},
    {"response": "Card not supported by Stripe", "status": "declined"},
    {"response": "Stripe processing error", "status": "declined"},
    {"response": "High risk transaction declined", "status": "declined"},
    {"response": "Insufficient Stripe balance", "status": "declined"}
]

stripe_db = load_database(STRIPE_DB_FILE)

@app.route('/stripe/key=<key>/cc=<card_data>', methods=['GET'])
def stripe_process(key, card_data):
    if key != API_KEY:
        return jsonify({"error": "Invalid authentication key"}), 401
    
    if not re.match(r'^\d{13,16}\|\d{2}\|\d{2,4}\|\d{3,4}$', card_data):
        return jsonify({"error": "Invalid card format. Use CC|MM|YY|CVV or CC|MM|YYYY|CVV"}), 400
    
    existing_tx = next((tx for tx in stripe_db["transactions"] if tx["cc"] == card_data), None)
    
    if existing_tx:
        result = {"response": existing_tx["response"], "status": existing_tx["status"]}
    else:
        # 2 out of 40 chance (5% approval rate)
        if random.randint(1, 40) <= 2:
            response_data = random.choice(STRIPE_APPROVED_RESPONSES)
        else:
            response_data = random.choice(STRIPE_DECLINED_RESPONSES)
        
        new_tx = {
            "cc": card_data,
            "response": response_data["response"],
            "status": response_data["status"],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        stripe_db["transactions"].append(new_tx)
        save_database(stripe_db, STRIPE_DB_FILE)
        result = {"response": response_data["response"], "status": response_data["status"]}
    
    time.sleep(random_delay())
    return jsonify({"cc": card_data, "response": result["response"], "status": result["status"]})

# ==============================================
# Arcenus Gateway
# ==============================================
ARCENUS_DB_FILE = "arcenus_transactions.json"

ARCENUS_APPROVED_RESPONSES = [
    {"response": "Arcenus payment processed", "status": "approved"},
    {"response": "Transaction approved by Arcenus", "status": "approved"}
]

ARCENUS_DECLINED_RESPONSES = [
    {"response": "Arcenus gateway timeout", "status": "declined"},
    {"response": "Invalid merchant configuration", "status": "declined"},
    {"response": "Daily transaction limit reached", "status": "declined"},
    {"response": "Arcenus fraud check failed", "status": "declined"},
    {"response": "Currency conversion not available", "status": "declined"}
]

arcenus_db = load_database(ARCENUS_DB_FILE)

@app.route('/arcenus/key=<key>/cc=<card_data>', methods=['GET'])
def arcenus_process(key, card_data):
    if key != API_KEY:
        return jsonify({"error": "Invalid authentication key"}), 401
    
    if not re.match(r'^\d{13,16}\|\d{2}\|\d{2,4}\|\d{3,4}$', card_data):
        return jsonify({"error": "Invalid card format. Use CC|MM|YY|CVV or CC|MM|YYYY|CVV"}), 400
    
    existing_tx = next((tx for tx in arcenus_db["transactions"] if tx["cc"] == card_data), None)
    
    if existing_tx:
        result = {"response": existing_tx["response"], "status": existing_tx["status"]}
    else:
        # 60% approval rate (120/200)
        if random.randint(1, 200) <= 120:
            response_data = random.choice(ARCENUS_APPROVED_RESPONSES)
        else:
            response_data = random.choice(ARCENUS_DECLINED_RESPONSES)
        
        new_tx = {
            "cc": card_data,
            "response": response_data["response"],
            "status": response_data["status"],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        arcenus_db["transactions"].append(new_tx)
        save_database(arcenus_db, ARCENUS_DB_FILE)
        result = {"response": response_data["response"], "status": response_data["status"]}
    
    time.sleep(random_delay())
    return jsonify({"cc": card_data, "response": result["response"], "status": result["status"]})

# ==============================================
# Random Stripe Gateway
# ==============================================
RANDOM_STRIPE_DB_FILE = "random_stripe_transactions.json"

RANDOM_STRIPE_APPROVED_RESPONSES = [
    {"response": "Charge successful", "status": "approved"}
]

RANDOM_STRIPE_DECLINED_RESPONSES = [
    {"response": "Stripe declined payment", "status": "declined"},
    {"response": "Card not supported", "status": "declined"},
    {"response": "Processing error occurred", "status": "declined"},
    {"response": "Bank declined transaction", "status": "declined"},
    {"response": "Insufficient funds", "status": "declined"}
]

random_stripe_db = load_database(RANDOM_STRIPE_DB_FILE)

@app.route('/random-stripe/key=<key>/cc=<card_data>', methods=['GET'])
def random_stripe_process(key, card_data):
    if key != API_KEY:
        return jsonify({"error": "Invalid authentication key"}), 401
    
    if not re.match(r'^\d{13,16}\|\d{2}\|\d{2,4}\|\d{3,4}$', card_data):
        return jsonify({"error": "Invalid card format. Use CC|MM|YY|CVV or CC|MM|YYYY|CVV"}), 400
    
    existing_tx = next((tx for tx in random_stripe_db["transactions"] if tx["cc"] == card_data), None)
    
    if existing_tx:
        result = {"response": existing_tx["response"], "status": existing_tx["status"]}
    else:
        # 1 out of 5 chance (20% approval rate)
        if random.randint(1, 5) == 1:
            response_data = random.choice(RANDOM_STRIPE_APPROVED_RESPONSES)
        else:
            response_data = random.choice(RANDOM_STRIPE_DECLINED_RESPONSES)
        
        new_tx = {
            "cc": card_data,
            "response": response_data["response"],
            "status": response_data["status"],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        random_stripe_db["transactions"].append(new_tx)
        save_database(random_stripe_db, RANDOM_STRIPE_DB_FILE)
        result = {"response": response_data["response"], "status": response_data["status"]}
    
    time.sleep(random_delay())
    return jsonify({"cc": card_data, "response": result["response"], "status": result["status"]})

# ==============================================
# RazorPay Gateway
# ==============================================
RAZORPAY_DB_FILE = "razorpay_transactions.json"

RAZORPAY_APPROVED_RESPONSES = [
    {"response": "RazorPay payment captured", "status": "approved"},
    {"response": "Transaction successful via RazorPay", "status": "approved"},
    {"response": "Payment authorized by RazorPay", "status": "approved"},
    {"response": "Funds transferred via RazorPay", "status": "approved"},
    {"response": "RazorPay charge completed", "status": "approved"}
]

RAZORPAY_DECLINED_RESPONSES = [
    {"response": "RazorPay authentication failed", "status": "declined"},
    {"response": "Payment method not supported", "status": "declined"},
    {"response": "RazorPay risk check failed", "status": "declined"},
    {"response": "Bank declined RazorPay request", "status": "declined"},
    {"response": "International payment not allowed", "status": "declined"},
    {"response": "RazorPay account limited", "status": "declined"},
    {"response": "Currency conversion failed", "status": "declined"},
    {"response": "Recurring payment not enabled", "status": "declined"},
    {"response": "UPI transaction failed", "status": "declined"},
    {"response": "Netbanking error occurred", "status": "declined"}
]

razorpay_db = load_database(RAZORPAY_DB_FILE)

@app.route('/razorpay/key=<key>/cc=<card_data>', methods=['GET'])
def razorpay_process(key, card_data):
    if key != API_KEY:
        return jsonify({"error": "Invalid authentication key"}), 401
    
    if not re.match(r'^\d{13,16}\|\d{2}\|\d{2,4}\|\d{3,4}$', card_data):
        return jsonify({"error": "Invalid card format. Use CC|MM|YY|CVV or CC|MM|YYYY|CVV"}), 400
    
    existing_tx = next((tx for tx in razorpay_db["transactions"] if tx["cc"] == card_data), None)
    
    if existing_tx:
        result = {"response": existing_tx["response"], "status": existing_tx["status"]}
    else:
        # 1 out of 42 chance (~2.4% approval rate)
        if random.randint(1, 42) == 1:
            response_data = random.choice(RAZORPAY_APPROVED_RESPONSES)
        else:
            response_data = random.choice(RAZORPAY_DECLINED_RESPONSES)
        
        new_tx = {
            "cc": card_data,
            "response": response_data["response"],
            "status": response_data["status"],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        razorpay_db["transactions"].append(new_tx)
        save_database(razorpay_db, RAZORPAY_DB_FILE)
        result = {"response": response_data["response"], "status": response_data["status"]}
    
    time.sleep(random_delay())
    return jsonify({"cc": card_data, "response": result["response"], "status": result["status"]})

# ==============================================
# PayU Gateway
# ==============================================
PAYU_DB_FILE = "payu_transactions.json"

PAYU_APPROVED_RESPONSES = [
    {"response": "PayU payment successful", "status": "approved"},
    {"response": "Transaction completed via PayU", "status": "approved"},
    {"response": "PayU instant settlement", "status": "approved"},
    {"response": "Payment captured by PayU", "status": "approved"},
    {"response": "PayU wallet credited", "status": "approved"},
    {"response": "PayU EMI processed", "status": "approved"},
    {"response": "PayU cashback applied", "status": "approved"}
]

PAYU_DECLINED_RESPONSES = [
    {"response": "PayU bank declined", "status": "declined"},
    {"response": "PayU fraud check failed", "status": "declined"},
    {"response": "PayU merchant limit reached", "status": "declined"},
    {"response": "PayU technical error", "status": "declined"},
    {"response": "PayU payment timeout", "status": "declined"},
    {"response": "PayU card bin blocked", "status": "declined"},
    {"response": "PayU duplicate transaction", "status": "declined"},
    {"response": "PayU invalid CVV", "status": "declined"},
    {"response": "PayU expired card", "status": "declined"},
    {"response": "PayU invalid OTP", "status": "declined"},
    {"response": "PayU 3DS failed", "status": "declined"},
    {"response": "PayU transaction declined", "status": "declined"}
]

payu_db = load_database(PAYU_DB_FILE)

@app.route('/payu/key=<key>/cc=<card_data>', methods=['GET'])
def payu_process(key, card_data):
    if key != API_KEY:
        return jsonify({"error": "Invalid authentication key"}), 401
    
    if not re.match(r'^\d{13,16}\|\d{2}\|\d{2,4}\|\d{3,4}$', card_data):
        return jsonify({"error": "Invalid card format. Use CC|MM|YY|CVV or CC|MM|YYYY|CVV"}), 400
    
    existing_tx = next((tx for tx in payu_db["transactions"] if tx["cc"] == card_data), None)
    
    if existing_tx:
        result = {"response": existing_tx["response"], "status": existing_tx["status"]}
    else:
        # 1 out of 30 chance (~3.3% approval rate)
        if random.randint(1, 30) == 1:
            response_data = random.choice(PAYU_APPROVED_RESPONSES)
        else:
            response_data = random.choice(PAYU_DECLINED_RESPONSES)
        
        new_tx = {
            "cc": card_data,
            "response": response_data["response"],
            "status": response_data["status"],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        payu_db["transactions"].append(new_tx)
        save_database(payu_db, PAYU_DB_FILE)
        result = {"response": response_data["response"], "status": response_data["status"]}
    
    time.sleep(random_delay())
    return jsonify({"cc": card_data, "response": result["response"], "status": result["status"]})

# ==============================================
# SK Gateway
# ==============================================
SK_DB_FILE = "sk_transactions.json"

SK_APPROVED_RESPONSES = [
    {"response": "SK payment processed", "status": "approved"},
    {"response": "SK transaction successful", "status": "approved"},
    {"response": "SK charge completed", "status": "approved"},
    {"response": "SK merchant approved", "status": "approved"},
    {"response": "SK payment captured", "status": "approved"}
]

SK_DECLINED_RESPONSES = [
    {"response": "SK bank declined", "status": "declined"},
    {"response": "SK fraud check failed", "status": "declined"},
    {"response": "SK merchant limit reached", "status": "declined"},
    {"response": "SK technical error", "status": "declined"},
    {"response": "SK payment timeout", "status": "declined"},
    {"response": "SK card bin blocked", "status": "declined"},
    {"response": "SK duplicate transaction", "status": "declined"},
    {"response": "SK invalid CVV", "status": "declined"},
    {"response": "SK expired card", "status": "declined"},
    {"response": "SK invalid OTP", "status": "declined"},
    {"response": "SK 3DS failed", "status": "declined"},
    {"response": "SK transaction declined", "status": "declined"},
    {"response": "SK regional restriction", "status": "declined"},
    {"response": "SK currency mismatch", "status": "declined"},
    {"response": "SK account frozen", "status": "declined"}
]

sk_db = load_database(SK_DB_FILE)

@app.route('/sk/key=<key>/cc=<card_data>', methods=['GET'])
def sk_process(key, card_data):
    if key != API_KEY:
        return jsonify({"error": "Invalid authentication key"}), 401
    
    if not re.match(r'^\d{13,16}\|\d{2}\|\d{2,4}\|\d{3,4}$', card_data):
        return jsonify({"error": "Invalid card format. Use CC|MM|YY|CVV or CC|MM|YYYY|CVV"}), 400
    
    existing_tx = next((tx for tx in sk_db["transactions"] if tx["cc"] == card_data), None)
    
    if existing_tx:
        result = {"response": existing_tx["response"], "status": existing_tx["status"]}
    else:
        # 5 out of 50 chance (10% approval rate)
        if random.randint(1, 50) <= 5:
            response_data = random.choice(SK_APPROVED_RESPONSES)
        else:
            response_data = random.choice(SK_DECLINED_RESPONSES)
        
        new_tx = {
            "cc": card_data,
            "response": response_data["response"],
            "status": response_data["status"],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        sk_db["transactions"].append(new_tx)
        save_database(sk_db, SK_DB_FILE)
        result = {"response": response_data["response"], "status": response_data["status"]}
    
    time.sleep(random_delay())
    return jsonify({"cc": card_data, "response": result["response"], "status": result["status"]})

# ==============================================
# PayPal Gateway
# ==============================================
PAYPAL_DB_FILE = "paypal_transactions.json"

PAYPAL_APPROVED_RESPONSES = [
    {"response": "PayPal payment completed", "status": "approved"},
    {"response": "PayPal transaction successful", "status": "approved"},
    {"response": "PayPal charge approved", "status": "approved"},
    {"response": "PayPal instant transfer", "status": "approved"},
    {"response": "PayPal balance updated", "status": "approved"}
]

PAYPAL_DECLINED_RESPONSES = [
    {"response": "PayPal bank declined", "status": "declined"},
    {"response": "PayPal fraud check failed", "status": "declined"},
    {"response": "PayPal account limited", "status": "declined"},
    {"response": "PayPal technical error", "status": "declined"},
    {"response": "PayPal payment timeout", "status": "declined"},
    {"response": "PayPal card bin blocked", "status": "declined"},
    {"response": "PayPal duplicate transaction", "status": "declined"},
    {"response": "PayPal invalid CVV", "status": "declined"},
    {"response": "PayPal expired card", "status": "declined"},
    {"response": "PayPal account restricted", "status": "declined"}
]

paypal_db = load_database(PAYPAL_DB_FILE)

@app.route('/paypal/key=<key>/cc=<card_data>', methods=['GET'])
def paypal_process(key, card_data):
    if key != API_KEY:
        return jsonify({"error": "Invalid authentication key"}), 401
    
    if not re.match(r'^\d{13,16}\|\d{2}\|\d{2,4}\|\d{3,4}$', card_data):
        return jsonify({"error": "Invalid card format. Use CC|MM|YY|CVV or CC|MM|YYYY|CVV"}), 400
    
    existing_tx = next((tx for tx in paypal_db["transactions"] if tx["cc"] == card_data), None)
    
    if existing_tx:
        result = {"response": existing_tx["response"], "status": existing_tx["status"]}
    else:
        # 5 out of 40 chance (12.5% approval rate)
        if random.randint(1, 40) <= 5:
            response_data = random.choice(PAYPAL_APPROVED_RESPONSES)
        else:
            response_data = random.choice(PAYPAL_DECLINED_RESPONSES)
        
        new_tx = {
            "cc": card_data,
            "response": response_data["response"],
            "status": response_data["status"],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        paypal_db["transactions"].append(new_tx)
        save_database(paypal_db, PAYPAL_DB_FILE)
        result = {"response": response_data["response"], "status": response_data["status"]}
    
    time.sleep(random_delay())
    return jsonify({"cc": card_data, "response": result["response"], "status": result["status"]})

# ==============================================
# Root route and info
# ==============================================
@app.route('/')
def index():
    return jsonify({
        "name": "Multi-Gateway Payment API",
        "version": "1.0",
        "api_key": API_KEY,
        "endpoints": {
            "auth_gateways": [
                "/chaos/key=<key>/cc=<card_data>",
                "/adyen/key=<key>/cc=<card_data>",
                "/app-auth/key=<key>/cc=<card_data>",
                "/payflow/key=<key>/cc=<card_data>",
                "/random/key=<key>/cc=<card_data>",
                "/shopify/key=<key>/cc=<card_data>",
                "/skrill/key=<key>/cc=<card_data>"
            ],
            "charge_gateways": [
                "/braintree/key=<key>/cc=<card_data>",
                "/stripe/key=<key>/cc=<card_data>",
                "/arcenus/key=<key>/cc=<card_data>",
                "/random-stripe/key=<key>/cc=<card_data>",
                "/razorpay/key=<key>/cc=<card_data>",
                "/payu/key=<key>/cc=<card_data>",
                "/sk/key=<key>/cc=<card_data>",
                "/paypal/key=<key>/cc=<card_data>"
            ]
        },
        "card_format": "CC|MM|YY|CVV or CC|MM|YYYY|CVV",
        "example": f"/chaos/key={API_KEY}/cc=4111111111111111|12|25|123"
    })

# ==============================================
# Main entry point
# ==============================================
if __name__ == '__main__':
    print(f"Starting Multi-Gateway Payment API on port {PORT}")
    print(f"API Key: {API_KEY}")
    print("\nAvailable endpoints:")
    print("Auth Gateways:")
    print("  - Chaos Auth: /chaos/key=<key>/cc=<card_data>")
    print("  - Adyen Auth: /adyen/key=<key>/cc=<card_data>")
    print("  - App Based Auth: /app-auth/key=<key>/cc=<card_data>")
    print("  - Payflow: /payflow/key=<key>/cc=<card_data>")
    print("  - Random Auth: /random/key=<key>/cc=<card_data>")
    print("  - Shopify: /shopify/key=<key>/cc=<card_data>")
    print("  - Skrill: /skrill/key=<key>/cc=<card_data>")
    print("\nCharge Gateways:")
    print("  - Braintree: /braintree/key=<key>/cc=<card_data>")
    print("  - Stripe: /stripe/key=<key>/cc=<card_data>")
    print("  - Arcenus: /arcenus/key=<key>/cc=<card_data>")
    print("  - Random Stripe: /random-stripe/key=<key>/cc=<card_data>")
    print("  - RazorPay: /razorpay/key=<key>/cc=<card_data>")
    print("  - PayU: /payu/key=<key>/cc=<card_data>")
    print("  - SK: /sk/key=<key>/cc=<card_data>")
    print("  - PayPal: /paypal/key=<key>/cc=<card_data>")
    print(f"\nExample: http://localhost:{PORT}/chaos/key={API_KEY}/cc=4111111111111111|12|25|123")
    
    app.run(host='0.0.0.0', port=PORT, threaded=True)
