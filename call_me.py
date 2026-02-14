import os
import sys
from twilio.rest import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get credentials
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
twilio_number = os.getenv('TWILIO_PHONE_NUMBER')
server_url = os.getenv('SERVER_URL')

# Use your demo number (your personal phone)
# We use the same number you set for the ambulance demo
your_phone_number = os.getenv('DEMO_PHONE_NUMBER2')

if not all([account_sid, auth_token, twilio_number, server_url, your_phone_number]):
    print("❌ Error: Missing configuration in .env")
    print("Make sure TWILIO credentials, SERVER_URL, and DEMO_PHONE_NUMBER are set.")
    sys.exit(1)

print(f"📞 Initiating call to {your_phone_number}...")

try:
    client = Client(account_sid, auth_token)

    call = client.calls.create(
        to=your_phone_number,
        from_=twilio_number,
        # This tells Twilio to fetch the voice instructions from your server
        url=f"{server_url}/incoming-call" 
    )

    print(f"✅ Call placed! SID: {call.sid}")
    print("📱 Check your phone, it should ring in a few seconds.")

except Exception as e:
    print(f"❌ Failed to make call: {e}")