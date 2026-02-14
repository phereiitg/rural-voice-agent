"""
Gemini Multimodal Live API Client
WebSocket-based client for real-time audio conversation
"""

import asyncio
import websockets
import json
import os
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class GeminiLiveClient:
    """Client for Gemini Multimodal Live API streaming"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")

        self.ws_url = (
            f"wss://generativelanguage.googleapis.com/ws/"
            f"google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent"
            f"?key={self.api_key}"
        )

        self.websocket = None
        self.model = "models/gemini-2.5-flash-native-audio-latest"
        self.is_connected = False

        logger.info("GeminiLiveClient initialized")

    async def connect(self):
        """Establish WebSocket connection and send setup configuration"""
        try:
            self.websocket = await websockets.connect(
                self.ws_url,
                ping_interval=20,
                ping_timeout=10
            )

            logger.info("WebSocket connected to Gemini Live API")

            # Send initial setup message
            setup_message = {
                "setup": {
                    "model": self.model,
                    "generation_config": {
                        "response_modalities": ["AUDIO"],
                        "speech_config": {
                            "voice_config": {
                                "prebuilt_voice_config": {
                                    "voice_name": "Puck"  # Voice for responses
                                }
                            }
                        }
                    },
                    "system_instruction": {
                        "parts": [{
                            "text": """You are a Hindi voice assistant for rural India. CRITICAL RULES:

RULE 1 - VOICE ONLY: You are a VOICE assistant. NEVER use markdown, bullet points, asterisks (**), headers, or formatted text. Speak naturally in plain Hindi only.

RULE 2 - NO THINKING OUT LOUD: NEVER narrate what you are about to do. NEVER say things like "I will now call...", "Let me analyze...", "I have gathered...". Just DO it silently and speak the result.

RULE 3 - SHORT ANSWERS: Keep every spoken response under 30 Hindi words.

RULE 4 - EMERGENCY (MOST IMPORTANT):
When user mentions any emergency (accident, pain, heart attack, etc.):
STEP 1: Ask name and location together in one short question. Example: "आपका नाम और जगह बताएं।"
STEP 2: As soon as you have the name AND location from the user, IMMEDIATELY call the call_ambulance function. Do NOT speak first. Call the function FIRST.
STEP 3: After the function returns, then say: "एम्बुलेंस बुलाई जा रही है। शांत रहें।"
NEVER ask for phone number — the system already has it.
NEVER write markdown or explain your reasoning.

RULE 5 - OTHER FUNCTIONS:
- Hospital search: call search_hospitals then speak results briefly
- Scheme info: call get_scheme_info then speak results briefly  
- Homework: call get_homework_help then speak results briefly

LANGUAGE: Always respond in Hindi. Short sentences. Natural speech only."""
                        }]
                    },
                    "tools": [{
                        "function_declarations": [
                            {
                                "name": "search_hospitals",
                                "description": "स्थान के आधार पर निकटतम अस्पताल खोजें",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "location": {
                                            "type": "string",
                                            "description": "जिला या शहर का नाम (जैसे: गुवाहाटी, असम)"
                                        },
                                        "hospital_type": {
                                            "type": "string",
                                            "enum": ["PHC", "CHC", "District", "Private", "Any"],
                                            "description": "अस्पताल का प्रकार"
                                        }
                                    },
                                    "required": ["location"]
                                }
                            },
                            {
                                "name": "get_scheme_info",
                                "description": "आयुष्मान भारत योजना की पात्रता और लाभ की जानकारी",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "query": {
                                            "type": "string",
                                            "description": "योजना के बारे में उपयोगकर्ता का सवाल"
                                        }
                                    },
                                    "required": ["query"]
                                }
                            },
                            {
                                "name": "get_homework_help",
                                "description": "NCERT पाठ्यक्रम के आधार पर होमवर्क में मदद",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "subject": {
                                            "type": "string",
                                            "enum": ["science", "maths", "social_studies", "hindi", "english"],
                                            "description": "विषय"
                                        },
                                        "class_number": {
                                            "type": "integer",
                                            "minimum": 6,
                                            "maximum": 12,
                                            "description": "कक्षा संख्या"
                                        },
                                        "question": {
                                            "type": "string",
                                            "description": "छात्र का सवाल"
                                        }
                                    },
                                    "required": ["question"]
                                }
                            },
                            {
                                "name": "call_ambulance",
                                "description": (
                                    "आपातकाल: एम्बुलेंस बुलाएं। "
                                    "पहले बातचीत में caller_name और location पूछें, "
                                    "फिर यह फंक्शन कॉल करें। "
                                    "फोन नंबर कभी मत पूछो — सिस्टम खुद लेता है।"
                                ),
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "caller_name": {
                                            "type": "string",
                                            "description": "मरीज या कॉलर का नाम (बातचीत से लिया गया)"
                                        },
                                        "location": {
                                            "type": "string",
                                            "description": "आपातकाल का स्थान (बातचीत से लिया गया)"
                                        },
                                        "emergency_type": {
                                            "type": "string",
                                            "description": "आपातकाल का प्रकार (जैसे: दिल का दौरा, दुर्घटना)"
                                        },
                                        "patient_condition": {
                                            "type": "string",
                                            "description": "मरीज की स्थिति का संक्षिप्त विवरण (वैकल्पिक)"
                                        }
                                    },
                                    "required": ["caller_name", "location", "emergency_type"]
                                }
                            }
                        ]
                    }]
                }
            }

            await self.websocket.send(json.dumps(setup_message))
            logger.info("Setup message sent to Gemini")

            # Wait for setup acknowledgement
            response = await self.websocket.recv()
            response_data = json.loads(response)
            logger.info(f"Gemini setup response: {response_data}")

            self.is_connected = True

        except Exception as e:
            logger.error(f"Error connecting to Gemini: {e}")
            raise

    async def send_audio(self, audio_base64: str):
        """Send audio chunk to Gemini for processing"""
        if not self.is_connected or not self.websocket:
            raise RuntimeError("Not connected to Gemini")

        try:
            message = {
                "realtime_input": {
                    "media_chunks": [{
                        "data": audio_base64,
                        "mime_type": "audio/pcm"
                    }]
                }
            }
            await self.websocket.send(json.dumps(message))

        except Exception as e:
            logger.error(f"Error sending audio to Gemini: {e}")
            raise

    async def send_text(self, text: str):
        """Send text message to Gemini"""
        if not self.is_connected or not self.websocket:
            raise RuntimeError("Not connected to Gemini")

        try:
            message = {
                "client_content": {
                    "turns": [{
                        "role": "user",
                        "parts": [{"text": text}]
                    }],
                    "turn_complete": True
                }
            }
            await self.websocket.send(json.dumps(message))
            logger.info(f"Text sent to Gemini: {text}")

        except Exception as e:
            logger.error(f"Error sending text to Gemini: {e}")
            raise

    async def send_function_response(
        self, function_call_id: str, function_name: str, result: dict
    ):
        """
        Send function execution result back to Gemini.
        Native-audio models use 'toolResponse' (camelCase) with 'functionResponses'.
        """
        try:
            message = {
                "toolResponse": {
                    "functionResponses": [{
                        "id": function_call_id,
                        "name": function_name,
                        "response": {"output": result}
                    }]
                }
            }
            await self.websocket.send(json.dumps(message))
            logger.info(f"Function response sent: {function_name}")

        except Exception as e:
            logger.error(f"Error sending function response: {e}")
            raise

    async def receive_messages(self, callback: Callable):
        """
        Listen for messages from Gemini and invoke callback.

        Args:
            callback: Async function to handle each message
        """
        if not self.is_connected or not self.websocket:
            raise RuntimeError("Not connected to Gemini")

        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await callback(data)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode message: {e}")
                except Exception as e:
                    logger.error(f"Error in message callback: {e}")

        except websockets.exceptions.ConnectionClosed:
            logger.warning("Gemini WebSocket connection closed")
            self.is_connected = False
        except Exception as e:
            logger.error(f"Error receiving messages: {e}")
            raise

    async def close(self):
        """Close WebSocket connection"""
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False
            logger.info("Gemini WebSocket connection closed")