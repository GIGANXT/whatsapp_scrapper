# Metal Price Dashboard

A real-time metal price dashboard that displays aluminum prices scraped from WhatsApp messages.

## Features

- Real-time metal price updates via WhatsApp messages
- Beautiful UI with live price cards
- Automatic data parsing and storage
- RESTful API for data access

## Tech Stack

- **Backend**: Flask (Python)
- **Frontend**: Next.js, React, TypeScript
- **Styling**: Tailwind CSS
- **Messaging**: Twilio WhatsApp API
- **Deployment**: ngrok for webhook tunneling

## Setup

### Backend Setup

1. Clone the repository
2. Create a virtual environment: `python -m venv .venv`
3. Activate the virtual environment:
   - Windows: `.venv\Scripts\activate`
   - macOS/Linux: `source .venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Create a `.env` file with your Twilio credentials:
   ```
   TWILIO_ACCOUNT_SID=your_account_sid
   TWILIO_AUTH_TOKEN=your_auth_token
   TWILIO_PHONE_NUMBER=your_twilio_phone_number
   ```
6. Run the Flask server: `python app.py`

### Frontend Setup

1. Navigate to the frontend directory: `cd STOCK-JK/frontend`
2. Install dependencies: `npm install` or `yarn install`
3. Run the development server: `npm run dev` or `yarn dev`

## Usage

1. Send a WhatsApp message to your Twilio number with the format:
   ```
   *Aluminium* 2679.00 (+14.00)
   ```
2. The dashboard will automatically update with the new price data

## API Endpoints

- `GET /api/price-data`: Get the latest metal price data
- `POST /webhook`: Twilio webhook for receiving WhatsApp messages

## License

MIT 