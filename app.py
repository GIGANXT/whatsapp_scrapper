from dotenv import load_dotenv
import os
from flask import Flask, request, Response, jsonify
from twilio.twiml.messaging_response import MessagingResponse
from flask_cors import CORS
import re
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global variable to store the latest price data
latest_price_data = {
    'spot_price': None,
    'price_change': None,
    'change_percentage': None,
    'last_updated': None
}

def parse_metal_price(message):
    """Function to parse metal price message"""
    try:
        print(f"Parsing message: {message}")
        
        # More lenient pattern that doesn't require MCX section
        aluminium_match = re.search(r'\*\s*Aluminium\s*\*\s*(\d+(?:\.\d+)?)\s*\(([+-]?\d+(?:\.\d+)?)\)', message)
        print(f"Regex match result: {aluminium_match}")
        
        if aluminium_match:
            result = {
                'price': float(aluminium_match.group(1)),
                'change': float(aluminium_match.group(2))
            }
            print(f"Parsed result: {result}")
            return result
            
        # If no match, try a more lenient pattern
        print("Trying more lenient pattern...")
        aluminium_match = re.search(r'Aluminium\s*(\d+(?:\.\d+)?)\s*\(([+-]?\d+(?:\.\d+)?)\)', message)
        print(f"Lenient regex match result: {aluminium_match}")
        
        if aluminium_match:
            result = {
                'price': float(aluminium_match.group(1)),
                'change': float(aluminium_match.group(2))
            }
            print(f"Parsed result from lenient pattern: {result}")
            return result
            
        print("No Aluminium price pattern found")
        return None
    except Exception as error:
        print(f'Error parsing message: {error}')
        print(f'Message type: {type(message)}')
        print(f'Message content: {message}')
        return None

@app.before_request
def log_request_info():
    """Log request details before processing"""
    print('\n=== Incoming Request ===')
    print(f'Time: {datetime.now().isoformat()}')
    print(f'Method: {request.method}')
    print(f'URL: {request.url}')
    print('Headers:', dict(request.headers))
    print('Form Data:', request.form.to_dict() if request.form else None)
    print('JSON Data:', request.get_json(silent=True))
    print('Raw Data:', request.get_data(as_text=True))
    print('=====================\n')

@app.route('/')
def home():
    """Root endpoint for testing"""
    print('Root endpoint accessed')
    return 'WhatsApp Metal Price Parser is running!'

@app.route('/api/price-data', methods=['GET'])
def get_price_data():
    """API endpoint to get the latest price data"""
    global latest_price_data
    
    if latest_price_data['spot_price'] is None:
        return jsonify({
            'error': 'No price data available yet'
        }), 404
    
    return jsonify(latest_price_data)

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    """Webhook endpoint for both GET and POST requests"""
    global latest_price_data
    
    print('\n=== Processing Webhook ===')
    print(f'Time: {datetime.now().isoformat()}')
    print('Method:', request.method)
    print('Headers:', dict(request.headers))
    print('Form Data:', request.form.to_dict() if request.form else None)
    print('JSON Data:', request.get_json(silent=True))
    print('Raw Data:', request.get_data(as_text=True))
    
    # For GET requests, just return a success message
    if request.method == 'GET':
        print('Handling GET request to webhook')
        return 'Webhook endpoint is working! Send a POST request with a message to parse metal prices.'
    
    # For POST requests, check the type of request
    print('Handling POST request to webhook')
    twiml = MessagingResponse()
    
    try:
        # Get the request data based on content type
        if request.is_json:
            data = request.get_json()
            print('Received JSON data:', data)
            message_body = data.get('Body')
        else:
            data = request.form.to_dict()
            print('Received form data:', data)
            message_body = data.get('Body')
        
        # Check if this is a status update
        if data.get('MessageStatus'):
            print('Received status update:', data.get('MessageStatus'))
            return 'OK'
        
        print('Message body:', message_body)
        
        if not message_body:
            print('No message body found')
            return 'OK'
        
        # Parse the metal price
        result = parse_metal_price(message_body)
        print('Parse result:', result)
        
        if result:
            # Store the values in variables
            spot_price = result['price']
            price_change = result['change']
            change_percentage = (price_change / spot_price) * 100
            
            # Update the global price data
            latest_price_data = {
                'spot_price': spot_price,
                'price_change': price_change,
                'change_percentage': change_percentage,
                'last_updated': datetime.now().isoformat()
            }
            
            # Print the values in a formatted way
            print('\n=== Scraped Metal Price Data ===')
            print(f'Spot Price: {spot_price:.2f}')
            print(f'Price Change: {price_change:.2f}')
            print(f'Change Percentage: {change_percentage:.2f}%')
            print('==============================\n')
            
            # Format the response using the new format
            response_message = f"spotPrice = {spot_price:.2f},\nchange = {price_change:.2f},\nchangePercent = {change_percentage:.2f},"
            print('Response message:', response_message)
            twiml.message(response_message)
        else:
            print('Could not parse metal price data')
            twiml.message('Sorry, could not parse the metal price data from the message.')
    except Exception as e:
        print(f'Error in webhook: {str(e)}')
        import traceback
        print(f'Traceback: {traceback.format_exc()}')
        twiml.message('An error occurred while processing your message.')
    
    print('=== Webhook Processing Complete ===\n')
    return Response(str(twiml), mimetype='text/xml')

@app.route('/status', methods=['GET', 'POST'])
def status():
    """Status callback endpoint for both GET and POST requests"""
    print('\n=== Status Update ===')
    print('Method:', request.method)
    
    # For GET requests, just return a success message
    if request.method == 'GET':
        print('Handling GET request to status endpoint')
        return 'Status endpoint is working! This endpoint receives status updates for sent messages.'
    
    # For POST requests, process the status update
    print('Handling POST request to status endpoint')
    
    # Get the request data based on content type
    if request.is_json:
        data = request.get_json()
        print('Received JSON data:', data)
    else:
        data = request.form.to_dict()
        print('Received form data:', data)
    
    print('Status:', data.get('MessageStatus'))
    print('SID:', data.get('MessageSid'))
    print('To:', data.get('To'))
    print('From:', data.get('From'))
    print('Body:', data.get('Body'))
    print('=== Status Update Complete ===\n')
    return 'OK'

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Not Found',
        'message': str(error)
    }), 404

@app.errorhandler(Exception)
def handle_error(error):
    """Error handling middleware"""
    print(f"Error occurred: {str(error)}")
    print(f"Error type: {type(error)}")
    import traceback
    print(f"Traceback: {traceback.format_exc()}")
    return jsonify({
        'error': 'Internal Server Error',
        'message': str(error)
    }), 500

# Catch-all route for undefined paths
@app.route('/<path:path>')
def catch_all(path):
    return jsonify({
        'error': 'Not Found',
        'message': f'The path /{path} does not exist'
    }), 404

if __name__ == '__main__':
    port = int(os.getenv('PORT', 3232))
    server_url = "148.135.138.22"  # Your VPS IP address
    print(f'Server is running on port {port}')
    print(f'Webhook URL: http://{server_url}/webhook')
    print(f'Status Callback URL: http://{server_url}/status')
    print(f'API URL: http://{server_url}/api/price-data')
    app.run(host='0.0.0.0', port=port, debug=False)  # Set debug to False in production
