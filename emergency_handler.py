"""
Emergency Handler Module
Handles emergency situations and ambulance calling.

Demo Mode:
  Set DEMO_MODE=true and DEMO_PHONE_NUMBER=+91XXXXXXXXXX in .env
  to route calls to your own number instead of 108.
  When your phone rings, Twilio reads out the patient name,
  location, and caller number automatically via /ambulance-briefing.
"""

import os
import logging
import requests
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class EmergencyHandler:
    """Handles emergency detection and ambulance calling"""

    def __init__(self):
        self.exotel_sid = os.getenv("EXOTEL_SID")
        self.exotel_token = os.getenv("EXOTEL_TOKEN")
        self.exotel_number = os.getenv("EXOTEL_NUMBER")
        self.ambulance_number = os.getenv("AMBULANCE_NUMBER", "+911082345678")

        # --- Demo Mode ---
        # Set DEMO_MODE=true in .env to route calls to your own number
        # instead of the real ambulance (108). Safe for demos/hackathons.
        self.demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
        self.demo_phone = os.getenv("DEMO_PHONE_NUMBER", "")  # e.g. +919876543210

        if self.demo_mode:
            if not self.demo_phone:
                logger.warning("⚠️  DEMO_MODE is ON but DEMO_PHONE_NUMBER is not set!")
            else:
                logger.warning(
                    f"🧪 DEMO_MODE is ON — emergency calls will go to "
                    f"{self.demo_phone} instead of 108"
                )
                self.ambulance_number = self.demo_phone  # override target

        self.emergency_keywords = [
            "दुर्घटना", "accident", "चोट", "injury", "खून", "blood",
            "दर्द", "pain", "बेहोश", "unconscious", "सांस", "breathing",
            "दिल का दौरा", "heart attack", "स्ट्रोक", "stroke",
            "जहर", "poison", "आग", "fire", "जल", "burn"
        ]

        logger.info("EmergencyHandler initialized")

    def detect_emergency(self, text: str) -> bool:
        """
        Detect if text contains emergency keywords.

        Args:
            text: Transcribed text from conversation

        Returns:
            True if emergency detected
        """
        text_lower = text.lower()
        for keyword in self.emergency_keywords:
            if keyword in text_lower:
                logger.warning(f"Emergency keyword detected: {keyword}")
                return True
        return False

    async def call_ambulance(
        self,
        user_phone: str,
        location: str,
        emergency_type: str,
        caller_name: Optional[str] = None,
        patient_condition: Optional[str] = None,
    ) -> Dict:
        """
        Initiate ambulance call via Exotel.

        In DEMO_MODE, calls DEMO_PHONE_NUMBER. When that call is answered,
        Exotel fetches /ambulance-briefing on this server and Twilio speaks
        the patient details aloud: name, location, caller number, condition.

        Args:
            user_phone:        Caller's phone (auto-captured from Twilio metadata —
                               AI never asks the user for this)
            location:          Emergency location (collected by AI in conversation)
            emergency_type:    Type of emergency (e.g. दुर्घटना, दिल का दौरा)
            caller_name:       Patient/caller name (collected by AI in conversation)
            patient_condition: Optional brief description of condition

        Returns:
            Dict with call status
        """
        try:
            if self.demo_mode:
                logger.warning(
                    f"🧪 [DEMO MODE] Routing emergency call to "
                    f"{self.demo_phone} instead of 108"
                )
                logger.critical("🚨 [DEMO] EMERGENCY CALL INITIATED")
            else:
                logger.critical("🚨 EMERGENCY CALL INITIATED")

            logger.critical(f"Caller Name : {caller_name or 'Unknown'}")
            logger.critical(f"Location    : {location}")
            logger.critical(f"Type        : {emergency_type}")
            logger.critical(f"Caller Phone: {user_phone}")

            # Log to file
            self._log_emergency(
                user_phone, location, emergency_type,
                patient_condition, caller_name
            )

            # Guard: Exotel credentials must be present
            if not all([self.exotel_sid, self.exotel_token, self.exotel_number]):
                logger.error("Exotel credentials not configured")
                return {
                    "success": False,
                    "message": "कृपया सीधे 108 पर कॉल करें। एम्बुलेंस ऑटो-कॉल उपलब्ध नहीं है।",
                    "manual_number": "108",
                }

            # Guard: demo phone must be set when in demo mode
            if self.demo_mode and not self.demo_phone:
                logger.error("DEMO_MODE is ON but DEMO_PHONE_NUMBER is not configured")
                return {
                    "success": False,
                    "message": "[DEMO] DEMO_PHONE_NUMBER not set in .env. Please add it.",
                    "demo_mode": True,
                }

            call_target = self.ambulance_number  # already overridden to demo_phone if demo
            logger.info(
                f"Placing call to: {call_target} "
                f"{'[DEMO]' if self.demo_mode else '[REAL 108]'}"
            )

            # ---------------------------------------------------------------
            # Build the TwiML briefing URL.
            # When the call is answered (by you in demo, or 108 in production),
            # Exotel fetches this URL. Our /ambulance-briefing endpoint returns
            # TwiML that speaks the patient details aloud in Hindi, e.g.:
            #   "सावधान! आपातकालीन कॉल। मरीज का नाम: अमित।
            #    स्थान: एम.जी. रोड। कॉलर नंबर: +9199xxxx"
            # ---------------------------------------------------------------
            server_url = os.getenv("SERVER_URL", "")
            briefing_url = (
                f"{server_url}/ambulance-briefing"
                f"?name={requests.utils.quote(caller_name or 'अज्ञात', safe='')}"
                f"&location={requests.utils.quote(location, safe='')}"
                f"&emergency={requests.utils.quote(emergency_type, safe='')}"
                f"&phone={requests.utils.quote(user_phone, safe='')}"
                f"&condition={requests.utils.quote(patient_condition or '', safe='')}"
            )
            logger.info(f"Briefing URL: {briefing_url}")

            # Exotel API call
            url = (
                f"https://api.exotel.com/v1/Accounts/"
                f"{self.exotel_sid}/Calls/connect"
            )
            payload = {
                "From": self.exotel_number,
                "To": call_target,
                "CallerId": user_phone,
                "Url": briefing_url,      # ← spoken when the call is picked up
                "StatusCallback": f"{server_url}/call-status",
                "CustomField": (
                    f"Emergency:{emergency_type}|Location:{location}"
                    f"|Caller:{caller_name}|Demo:{self.demo_mode}"
                ),
            }

            response = requests.post(
                url,
                auth=(self.exotel_sid, self.exotel_token),
                data=payload,
                timeout=10,
            )

            if response.status_code == 200:
                call_data = response.json()
                call_sid = call_data.get("Call", {}).get("Sid", "Unknown")
                name_part = f" {caller_name}" if caller_name else ""

                if self.demo_mode:
                    logger.warning(
                        f"🧪 [DEMO] Call placed to {self.demo_phone} "
                        f"successfully: {call_sid}"
                    )
                else:
                    logger.info(f"Ambulance call initiated: {call_sid}")

                return {
                    "success": True,
                    "message": (
                        f"एम्बुलेंस बुलाई जा रही है {location} के लिए। "
                        f"शांत रहें{name_part}। मदद आ रही है।"
                    ),
                    "call_sid": call_sid,
                    "demo_mode": self.demo_mode,
                    "called_number": call_target,
                    "instructions": (
                        "साँस लेते रहें। घबराएं नहीं। "
                        "एम्बुलेंस 15-20 मिनट में पहुंचेगी।"
                    ),
                }
            else:
                logger.error(
                    f"Exotel API error: {response.status_code} - {response.text}"
                )
                return {
                    "success": False,
                    "message": "ऑटो-कॉल में समस्या। कृपया तुरंत 108 डायल करें!",
                    "manual_number": "108",
                    "fallback": True,
                }

        except requests.exceptions.Timeout:
            logger.error("Exotel API timeout")
            return {
                "success": False,
                "message": "कनेक्शन में देरी। कृपया सीधे 108 पर कॉल करें!",
                "manual_number": "108",
            }
        except Exception as e:
            logger.error(f"Error calling ambulance: {e}")
            return {
                "success": False,
                "message": "एम्बुलेंस कॉल में त्रुटि। तुरंत 108 डायल करें!",
                "manual_number": "108",
                "error": str(e),
            }

    def _log_emergency(
        self,
        user_phone: str,
        location: str,
        emergency_type: str,
        patient_condition: Optional[str],
        caller_name: Optional[str] = None,
    ):
        """Log emergency to file for record keeping"""
        try:
            log_dir = "./data/emergency_logs"
            os.makedirs(log_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = (
                f"\n{'='*50}\n"
                f"{'[DEMO MODE] ' if self.demo_mode else ''}EMERGENCY LOG\n"
                f"{'='*50}\n"
                f"Timestamp  : {timestamp}\n"
                f"Caller Name: {caller_name or 'Unknown'}\n"
                f"Phone      : {user_phone}\n"
                f"Location   : {location}\n"
                f"Type       : {emergency_type}\n"
                f"Condition  : {patient_condition or 'Not specified'}\n"
                f"Demo Mode  : {self.demo_mode}\n"
                f"Called No  : {self.ambulance_number}\n"
                f"{'='*50}\n"
            )

            log_file = os.path.join(
                log_dir,
                f"emergencies_{datetime.now().strftime('%Y%m%d')}.log"
            )
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)

            logger.info(f"Emergency logged to {log_file}")

        except Exception as e:
            logger.error(f"Failed to log emergency: {e}")

    def get_safety_instructions(self, emergency_type: str) -> str:
        """
        Get immediate safety instructions based on emergency type.

        Args:
            emergency_type: Type of emergency

        Returns:
            Safety instructions in Hindi
        """
        instructions = {
            "दिल का दौरा": (
                "तुरंत बैठ जाएं या लेट जाएं। "
                "तंग कपड़े ढीले करें। "
                "अगर दवा है तो लें। "
                "घबराएं नहीं, एम्बुलेंस आ रही है।"
            ),
            "दुर्घटना": (
                "हिलें नहीं। "
                "अगर खून बह रहा है तो साफ कपड़े से दबाएं। "
                "शांत रहें, मदद आ रही है।"
            ),
            "सांस की तकलीफ": (
                "सीधे बैठें। "
                "धीरे-धीरे गहरी सांस लें। "
                "घबराएं नहीं। "
                "खिड़की खोलें ताज़ी हवा के लिए।"
            ),
            "बेहोशी": (
                "व्यक्ति को करवट के बल लिटाएं। "
                "सांस चेक करें। "
                "कुछ भी खिलाने की कोशिश न करें। "
                "एम्बुलेंस का इंतजार करें।"
            ),
            "default": (
                "शांत रहें। "
                "सुरक्षित जगह पर रहें। "
                "एम्बुलेंस आ रही है। "
                "मदद 15-20 मिनट में पहुंचेगी।"
            ),
        }

        return instructions.get(emergency_type, instructions["default"])


# Global instance
emergency_handler = EmergencyHandler()