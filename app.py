from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from twilio.rest import Client
import requests
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

# Database Model
class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    currency_pair = db.Column(db.String(10), nullable=False)
    threshold = db.Column(db.Float, nullable=False)
    direction = db.Column(db.String(2), nullable=False)  # '>' or '<'
    phone_number = db.Column(db.String(20), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<Alert {self.currency_pair} {self.direction} {self.threshold}>'

# Initialize database
with app.app_context():
    db.create_all()

# Twilio client
twilio_client = Client(app.config['TWILIO_ACCOUNT_SID'], app.config['TWILIO_AUTH_TOKEN'])

def get_forex_rate(currency_pair):
    """Fetch current forex rate from Alpha Vantage API"""
    from_currency, to_currency = currency_pair.split('/')
    
    params = {
        'function': 'CURRENCY_EXCHANGE_RATE',
        'from_currency': from_currency,
        'to_currency': to_currency,
        'apikey': app.config['ALPHA_VANTAGE_API_KEY']
    }
    
    response = requests.get(app.config['BASE_URL'], params=params)
    data = response.json()
    
    try:
        rate = float(data['Realtime Currency Exchange Rate']['5. Exchange Rate'])
        return rate
    except (KeyError, ValueError):
        print(f"Error fetching rate for {currency_pair}: {data}")
        return None

def check_alerts():
    """Check all active alerts against current rates"""
    with app.app_context():
        active_alerts = Alert.query.filter_by(is_active=True).all()
        
        for alert in active_alerts:
            current_rate = get_forex_rate(alert.currency_pair)
            if current_rate is None:
                continue
                
            condition_met = False
            if alert.direction == '>' and current_rate > alert.threshold:
                condition_met = True
            elif alert.direction == '<' and current_rate < alert.threshold:
                condition_met = True
                
            if condition_met:
                send_alert(alert, current_rate)
                alert.is_active = False  # Deactivate after triggering
                db.session.commit()

def send_alert(alert, current_rate):
    """Send SMS alert via Twilio"""
    message = (
        f"Forex Alert: {alert.currency_pair} is now {current_rate:.4f}, "
        f"which is {alert.direction} your threshold of {alert.threshold:.4f}"
    )
    
    try:
        twilio_client.messages.create(
            body=message,
            from_=app.config['TWILIO_PHONE_NUMBER'],
            to=alert.phone_number
        )
        print(f"Alert sent to {alert.phone_number}")
    except Exception as e:
        print(f"Failed to send alert: {e}")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        currency_pair = request.form['currency_pair'].upper()
        threshold = float(request.form['threshold'])
        direction = request.form['direction']
        phone_number = request.form['phone_number']
        
        # Validate currency pair format (e.g., EUR/USD)
        if '/' not in currency_pair or len(currency_pair.split('/')) != 2:
            flash('Invalid currency pair format. Use format like EUR/USD', 'error')
            return redirect(url_for('index'))
        
        # Create new alert
        new_alert = Alert(
            currency_pair=currency_pair,
            threshold=threshold,
            direction=direction,
            phone_number=phone_number
        )
        
        db.session.add(new_alert)
        db.session.commit()
        
        flash('Alert created successfully!', 'success')
        return redirect(url_for('index'))
    
    alerts = Alert.query.all()
    return render_template('index.html', alerts=alerts)

@app.route('/delete/<int:alert_id>', methods=['POST'])
def delete_alert(alert_id):
    alert = Alert.query.get_or_404(alert_id)
    db.session.delete(alert)
    db.session.commit()
    flash('Alert deleted successfully!', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
