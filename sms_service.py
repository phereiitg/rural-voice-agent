"""
SMS Service Module
Sends SMS summaries and notifications via Twilio
"""

import os
import logging
from typing import Optional
from twilio.rest import Client

logger = logging.getLogger(__name__)


class SMSService:
    """Handles SMS sending via Twilio"""
    
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_PHONE_NUMBER")
        
        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
            logger.info("SMS Service initialized")
        else:
            self.client = None
            logger.warning("Twilio credentials not found - SMS service disabled")
    
    async def send_sms(self, to_number: str, message: str) -> dict:
        """
        Send SMS message
        
        Args:
            to_number: Recipient phone number (with country code)
            message: SMS message text (max 160 characters recommended)
            
        Returns:
            Dict with send status
        """
        if to_number == self.from_number:
            logger.warning(f"Skipping SMS — to/from are the same number. Use a different phone.")
            return {"success": False, "error": "to/from same number"}
        if not self.client:
            logger.error("SMS service not configured")
            return {
                "success": False,
                "error": "SMS service not configured"
            }
        
        try:
            # Truncate message if too long
            if len(message) > 160:
                message = message[:157] + "..."
            
            message_obj = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_number
            )
            
            logger.info(f"SMS sent successfully to {to_number}: {message_obj.sid}")
            
            return {
                "success": True,
                "sid": message_obj.sid,
                "status": message_obj.status
            }
            
        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_call_summary(
        self,
        to_number: str,
        hospitals: Optional[list] = None,
        scheme_info: bool = False,
        homework_help: bool = False
    ) -> dict:
        """
        Send call summary SMS with relevant information
        
        Args:
            to_number: User's phone number
            hospitals: List of hospitals mentioned in call
            scheme_info: Whether scheme info was discussed
            homework_help: Whether homework help was provided
            
        Returns:
            Dict with send status
        """
        message = "कॉल सारांश:\n"
        
        if hospitals:
            message += f"अस्पताल: {hospitals[0].get('name', 'N/A')}\n"
            message += f"फोन: {hospitals[0].get('phone', 'N/A')}\n"
        
        if scheme_info:
            message += "आयुष्मान: 14555\n"
        
        if homework_help:
            message += "NCERT पुस्तकें देखें\n"
        
        message += "धन्यवाद! 🙏"
        
        return await self.send_sms(to_number, message)
    
    async def send_emergency_alert(
        self,
        to_number: str,
        location: str,
        emergency_type: str
    ) -> dict:
        """
        Send emergency alert SMS
        
        Args:
            to_number: User's phone number
            location: Emergency location
            emergency_type: Type of emergency
            
        Returns:
            Dict with send status
        """
        message = (
            f"🚨 आपातकाल!\n"
            f"स्थान: {location}\n"
            f"प्रकार: {emergency_type}\n"
            f"एम्बुलेंस बुलाई गई है।\n"
            f"या 108 डायल करें।"
        )
        
        return await self.send_sms(to_number, message)


# Global instance
sms_service = SMSService()
