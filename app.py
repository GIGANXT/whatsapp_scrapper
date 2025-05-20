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

# Global variable to store the latest company price updates
latest_company_updates = {
    'Vedanta': None,
    'Hindalco': None,
    'NALCO': None
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

def parse_vedanta_update(message):
    """Function to parse Vedanta price update message"""
    try:
        print(f"Parsing Vedanta message: {message}")
        
        # Pattern for Vedanta: "Vedanta wef 08/05/2025 decreases the basic price of I/R/B by INR 2500 pmt"
        vedanta_pattern = re.compile(
            r'Vedanta\s+w\.?e\.?f\.?\s+(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})\s+'
            r'(increases?|decreases?)\s+the\s+basic\s+price\s+of.+?by\s+'
            r'(?:INR|Rs\.?|₹)?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:\/?)?\s*(pmt|PMT|MT|mt|per\s+ton)?', 
            re.IGNORECASE
        )
        
        match = vedanta_pattern.search(message)
        print(f"Vedanta regex match result: {match}")
        
        if match:
            date_str = match.group(1)
            action = match.group(2).lower()
            amount = float(match.group(3).replace(',', ''))
            unit = match.group(4).upper() if match.group(4) else "PMT"
            
            # Standardize the date format
            date_parts = re.split(r'[/.-]', date_str)
            if len(date_parts) == 3:
                day, month, year = date_parts
                # Ensure 4-digit year
                if len(year) == 2:
                    year = '20' + year
                effective_date = f"{day.zfill(2)}/{month.zfill(2)}/{year}"
            else:
                effective_date = date_str
            
            # Determine sign based on action
            sign = "-" if "decrease" in action else "+"
            
            result = {
                'company': 'Vedanta',
                'action': action,
                'amount': amount,
                'sign': sign,
                'unit': unit,
                'effective_date': effective_date
            }
            print(f"Parsed Vedanta result: {result}")
            return result
            
        print("No Vedanta pattern found")
        return None
    except Exception as error:
        print(f'Error parsing Vedanta message: {error}')
        return None

def parse_hindalco_update(message):
    """Function to parse Hindalco price update message"""
    try:
        print(f"Parsing Hindalco message: {message}")
        
        # Pattern for Hindalco: "Hindalco Prices of our all-primary products have been increased by Rs. 6,500/MT wef 10thh May 2025."
        hindalco_pattern = re.compile(
            r'Hindalco.+?(increased|decreased)\s+by\s+(?:Rs\.?|INR|₹)?\s*'
            r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:\/?)?\s*(MT|mt|PMT|pmt|per\s+ton)?\s+'
            r'w\.?e\.?f\.?\s+(\d{1,2}(?:st|nd|rd|th)?h?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})',
            re.IGNORECASE
        )
        
        match = hindalco_pattern.search(message)
        print(f"Hindalco regex match result: {match}")
        
        if match:
            action = match.group(1).lower()
            amount = float(match.group(2).replace(',', ''))
            unit = match.group(3).upper() if match.group(3) else "MT"
            date_str = match.group(4)
            
            # Extract numeric day, month name, and year from date string
            day_match = re.search(r'(\d{1,2})', date_str)
            month_match = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*', date_str, re.IGNORECASE)
            year_match = re.search(r'(\d{2,4})$', date_str)
            
            day = day_match.group(1) if day_match else "01"
            month_name = month_match.group(1) if month_match else "Jan"
            year = year_match.group(1) if year_match else "2025"
            
            # Convert month name to number
            month_dict = {
                'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'may': '05', 'jun': '06',
                'jul': '07', 'aug': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
            }
            month = month_dict.get(month_name.lower()[:3], '01')
            
            # Ensure 4-digit year
            if len(year) == 2:
                year = '20' + year
                
            effective_date = f"{day.zfill(2)}/{month}/{year}"
            
            # Determine sign based on action
            sign = "-" if "decrease" in action else "+"
            
            result = {
                'company': 'Hindalco',
                'action': action,
                'amount': amount,
                'sign': sign,
                'unit': unit,
                'effective_date': effective_date
            }
            print(f"Parsed Hindalco result: {result}")
            return result
            
        print("No Hindalco pattern found")
        return None
    except Exception as error:
        print(f'Error parsing Hindalco message: {error}')
        return None

def parse_nalco_update(message):
    """Function to parse NALCO price update message"""
    try:
        print(f"Parsing NALCO message: {message}")
        
        # Pattern for NALCO: "NALCO w.e.f. 14.05.2025 increases the basic price of All Aluminium Metal Products by Rs 9100/-PMT"
        nalco_pattern = re.compile(
            r'NALCO\s+w\.?e\.?f\.?\s+(\d{1,2}\.?\/?-?\d{1,2}\.?\/?-?\d{2,4})\s+'
            r'(increases?|decreases?)\s+.+?by\s+(?:Rs\.?|INR|₹)?\s*'
            r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:\/|-)?\s*(PMT|pmt|MT|mt|per\s+ton)?',
            re.IGNORECASE
        )
        
        match = nalco_pattern.search(message)
        print(f"NALCO regex match result: {match}")
        
        if match:
            date_str = match.group(1)
            action = match.group(2).lower()
            amount = float(match.group(3).replace(',', ''))
            unit = match.group(4).upper() if match.group(4) else "PMT"
            
            # Standardize the date format
            date_parts = re.split(r'[./-]', date_str)
            if len(date_parts) == 3:
                day, month, year = date_parts
                # Ensure 4-digit year
                if len(year) == 2:
                    year = '20' + year
                effective_date = f"{day.zfill(2)}/{month.zfill(2)}/{year}"
            else:
                effective_date = date_str
            
            # Determine sign based on action
            sign = "-" if "decrease" in action else "+"
            
            result = {
                'company': 'NALCO',
                'action': action,
                'amount': amount,
                'sign': sign,
                'unit': unit,
                'effective_date': effective_date
            }
            print(f"Parsed NALCO result: {result}")
            return result
            
        print("No NALCO pattern found")
        return None
    except Exception as error:
        print(f'Error parsing NALCO message: {error}')
        return None

def parse_metal_info_services(message):
    """Function to parse metal info services message format"""
    try:
        print(f"Parsing metal info services message: {message}")
        
        # Extract date from the message
        date_match = re.search(r'\*(\d{1,2}-\d{1,2}-\d{4})\*', message)
        if not date_match:
            print("No date found in message")
            return None
            
        date_str = date_match.group(1)
        # Convert date format from DD-MM-YYYY to YYYY-MM-DD
        day, month, year = date_str.split('-')
        formatted_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        # Look for CASH SETTLEMENT section and stop at 3-MONTH
        cash_section = re.search(r'\*CASH SETTLMENT\*(.*?)(?:\*3-MONTH\*|\*📣)', message, re.DOTALL)
        if not cash_section:
            print("No CASH SETTLEMENT section found")
            return None
            
        # Extract Aluminium price from CASH SETTLEMENT section
        aluminium_match = re.search(r'\*Aluminium\*:\s*(\d+(?:\.\d+)?)', cash_section.group(1))
        if not aluminium_match:
            print("No Aluminium price found in CASH SETTLEMENT section")
            return None
            
        price = float(aluminium_match.group(1))
        current_time = datetime.now().strftime('%H:%M:%S')
        
        result = {
            'price': price,
            'date': formatted_date,
            'time': current_time,
            'type': 'cash_settlement'  # Add type to identify it's cash settlement
        }
        print(f"Parsed metal info services result: {result}")
        return result
        
    except Exception as error:
        print(f'Error parsing metal info services message: {error}')
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

@app.route('/api/company-updates', methods=['GET'])
def get_company_updates():
    """API endpoint to get the latest company updates"""
    global latest_company_updates
    
    # Check if any updates are available
    if not any(latest_company_updates.values()):
        return jsonify({
            'error': 'No company updates available yet'
        }), 404
    
    return jsonify(latest_company_updates)

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    """Webhook endpoint for both GET and POST requests"""
    global latest_price_data, latest_company_updates
    
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
        response = 'Webhook endpoint is working! Send a POST request with a message to parse metal prices.'
        print(f'Response: {response}')
        return response
    
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
            response = 'OK'
            print(f'Response: {response}')
            return response
        
        print('Message body:', message_body)
        
        if not message_body:
            print('No message body found')
            response = 'OK'
            print(f'Response: {response}')
            return response
        
        # First try to parse as metal info services message
        metal_info_result = parse_metal_info_services(message_body)
        if metal_info_result and metal_info_result['type'] == 'cash_settlement':
            price = metal_info_result['price']
            date = metal_info_result['date']
            time = metal_info_result['time']
            
            # Update the global price data
            latest_price_data = {
                'spot_price': price,
                'price_change': None,  # No change data in this format
                'change_percentage': None,
                'last_updated': f"{date} {time}"
            }
            
            # Format the response
            response_message = f"cashSettlement = {price:.2f}\ndateTime = {date} {time}"
            print('Response message:', response_message)
            twiml.message(response_message)
            return Response(str(twiml), mimetype='text/xml')
        
        # If not metal info services, try company updates
        company_result = None
        for parser_func in [parse_vedanta_update, parse_hindalco_update, parse_nalco_update]:
            company_result = parser_func(message_body)
            if company_result:
                break
        
        # If we found a company update, handle it
        if company_result:
            print('Found company update:', company_result)
            company = company_result['company']
            amount = company_result['amount']
            sign = company_result['sign']
            effective_date = company_result['effective_date']
            current_time = datetime.now().strftime('%H:%M')
            
            # Store the company update
            latest_company_updates[company] = {
                'amount': amount,
                'sign': sign,
                'effective_date': effective_date,
                'last_updated': datetime.now().isoformat()
            }
            
            # Format the acknowledgment message
            response_message = f"{company}, {sign}{amount}, {effective_date} {current_time}"
            print('Company update response message:', response_message)
            twiml.message(response_message)
            return Response(str(twiml), mimetype='text/xml')
        
        # If not a company update, try to parse as a metal price update
        metal_result = parse_metal_price(message_body)
        print('Metal price parse result:', metal_result)
        
        if metal_result:
            # Metal price update
            spot_price = metal_result['price']
            price_change = metal_result['change']
            change_percentage = (price_change / spot_price) * 100
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
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
            
            # Format the response using the existing format
            response_message = f"spotPrice = {spot_price:.2f},\nchange = {price_change:.2f},\nchangePercent = {change_percentage:.2f},\ndateTime = {current_time}"
            print('Metal price response message:', response_message)
            twiml.message(response_message)
            return Response(str(twiml), mimetype='text/xml')
            
        print("No match found for any message type")
        twiml.message('Sorry, could not parse data from the message.')
    except Exception as e:
        print(f'Error in webhook: {str(e)}')
        import traceback
        print(f'Traceback: {traceback.format_exc()}')
        twiml.message('An error occurred while processing your message.')
    
    print('=== Webhook Processing Complete ===\n')
    response = Response(str(twiml), mimetype='text/xml')
    print(f'Response: {response}')
    return response

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
    print(f'API URL for metal prices: http://{server_url}/api/price-data')
    print(f'API URL for company updates: http://{server_url}/api/company-updates')
    app.run(host='0.0.0.0', port=port, debug=False)  # Set debug to False in production
