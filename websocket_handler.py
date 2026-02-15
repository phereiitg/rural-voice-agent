"""
WebSocket Handler Module
Bridges Twilio and Gemini WebSocket connections for real-time voice AI
"""

import asyncio
import os
import json
import logging
from datetime import datetime
from typing import Optional
from fastapi import WebSocket

from gemini_client import GeminiLiveClient
from audio_resampler import resampler
from rag_tools import rag_tools
from emergency_handler import emergency_handler
from sms_service import sms_service

logger = logging.getLogger(__name__)


class MediaStreamHandler:
    """
    Handles the bidirectional streaming between Twilio and Gemini
    
    Flow:
    1. User speaks → Twilio → Handler → Gemini
    2. Gemini responds → Handler → Twilio → User
    3. Function calls → RAG Tools → Back to Gemini
    """
    
    def __init__(self):
        self.gemini_client = GeminiLiveClient()
        self.rag_tools = rag_tools
        self.emergency_handler = emergency_handler
        self.sms_service = sms_service
        
        # Call state
        self.call_sid = None
        self.user_phone = None
        self.stream_sid = None
        
        # Conversation tracking
        self.conversation_transcript = []
        self.hospitals_mentioned = []
        self.scheme_discussed = False
        self.homework_provided = False
        self.emergency_triggered = False
        
        # WebSocket connections
        self.twilio_ws = None
        self.gemini_connected = False
        
        logger.info("MediaStreamHandler initialized")
    
    async def handle_stream(self, twilio_ws: WebSocket):
        """
        Main handler for Twilio WebSocket connection
        Manages the entire lifecycle of a voice call
        """
        try:
            # Accept Twilio WebSocket
            await twilio_ws.accept()
            self.twilio_ws = twilio_ws
            logger.info("Twilio WebSocket accepted")
            
            # Connect to Gemini
            await self.gemini_client.connect()
            self.gemini_connected = True
            logger.info(" Gemini WebSocket connected")
            
            # Run both loops concurrently
            await asyncio.gather(
                self.twilio_to_gemini_loop(),
                self.gemini_to_twilio_loop(),
                return_exceptions=True
            )
            
        except Exception as e:
            logger.error(f"Error in handle_stream: {e}")
        finally:
            await self.cleanup()
    
    async def twilio_to_gemini_loop(self):
        """
        Forward audio and events from Twilio to Gemini
        Handles: start, media, stop events
        """
        try:
            async for message in self.twilio_ws.iter_text():
                data = json.loads(message)
                event = data.get('event')
                
                if event == 'start':
                    await self.handle_call_start(data)
                
                elif event == 'media':
                    await self.handle_media_chunk(data)
                
                elif event == 'stop':
                    await self.handle_call_stop(data)
                    break
                
        except Exception as e:
            logger.error(f"Error in Twilio→Gemini loop: {e}")
    
    async def handle_call_start(self, data: dict):
        """Handle call start event from Twilio"""
        start_data = data.get('start', {})
        self.stream_sid = data.get('streamSid')
        self.call_sid = start_data.get('callSid')

        custom_params = start_data.get('customParameters', {})
        from_number = custom_params.get('From', '')
        to_number = custom_params.get('To', '')
        twilio_number = os.getenv('TWILIO_PHONE_NUMBER', '')

        # When call_me.py dials out, From = Twilio number, To = real person.
        # When someone calls in normally, From = real person, To = Twilio number.
        # So: the real user phone is whichever of From/To is NOT the Twilio number.
        if from_number and from_number != twilio_number:
            self.user_phone = from_number
        elif to_number and to_number != twilio_number:
            self.user_phone = to_number
        else:
            self.user_phone = from_number  # fallback

        logger.info(f"Call started: {self.call_sid}")
        logger.info(f" From: {from_number} | To: {to_number} | Twilio: {twilio_number}")
        logger.info(f" Real user phone: {self.user_phone}")
        logger.info(f" Stream: {self.stream_sid}")
    
    async def handle_media_chunk(self, data: dict):
        """
        Handle incoming audio chunk from Twilio
        Resample and forward to Gemini
        """
        try:
            media = data.get('media', {})
            mulaw_payload = media.get('payload')
            
            if not mulaw_payload:
                return
            
            # Convert: 8kHz μ-law → 16kHz PCM
            pcm_16k = resampler.twilio_to_gemini(mulaw_payload)
            
            # Send to Gemini
            if self.gemini_connected:
                await self.gemini_client.send_audio(pcm_16k)
                
        except Exception as e:
            logger.error(f"Error handling media chunk: {e}")
    
    async def handle_call_stop(self, data: dict):
        """Handle call end event"""
        logger.info(f"Call ended: {self.call_sid}")
        
        # Send SMS summary if user provided phone number
        if self.user_phone:
            try:
                await self.sms_service.send_call_summary(
                    to_number=self.user_phone,
                    hospitals=self.hospitals_mentioned,
                    scheme_info=self.scheme_discussed,
                    homework_help=self.homework_provided
                )
            except Exception as e:
                logger.error(f"Error sending SMS summary: {e}")
    
    async def gemini_to_twilio_loop(self):
        """
        Listen for responses from Gemini and forward to Twilio
        Handles: audio responses, function calls, transcripts
        """
        try:
            await self.gemini_client.receive_messages(self.handle_gemini_message)
        except Exception as e:
            logger.error(f"Error in Gemini→Twilio loop: {e}")
    
    async def handle_gemini_message(self, data: dict):
        """
        Process different types of messages from Gemini.

        The native-audio models send function calls in TWO possible locations:
          1. data['toolCall']['functionCalls']  ← native-audio model format
          2. data['serverContent']['modelTurn']['parts'][]['functionCall']  ← older format
        We handle both so nothing is missed.
        """
        try:
            # Setup complete
            if 'setupComplete' in data:
                logger.info("Gemini setup complete")
                return

            # ── Top-level toolCall (native-audio model format) ────────────────
            # This is how gemini-2.5-flash-native-audio-* actually fires tools.
            if 'toolCall' in data:
                tool_call = data['toolCall']
                for fc in tool_call.get('functionCalls', []):
                    logger.info(f"🔧 toolCall received: {fc.get('name')} | args: {fc.get('args')}")
                    await self.handle_function_call(fc)
                return  # toolCall messages don't have serverContent

            # ── serverContent (audio, text, older-style function calls) ───────
            if 'serverContent' in data:
                await self.handle_server_content(data['serverContent'])

            # Turn complete
            if data.get('turnComplete'):
                logger.debug("User turn complete")

        except Exception as e:
            logger.error(f"Error handling Gemini message: {e}")
    
    async def handle_server_content(self, content: dict):
        """
        Handle server content from Gemini
        Can contain: audio, text, or function calls
        """
        model_turn = content.get('modelTurn', {})
        parts = model_turn.get('parts', [])
        
        for part in parts:
            # Audio response from Gemini
            if 'inlineData' in part:
                await self.handle_audio_response(part['inlineData'])
            
            # Text transcript (for logging)
            if 'text' in part:
                await self.handle_text_response(part['text'])
            
            # Function call from Gemini
            if 'functionCall' in part:
                await self.handle_function_call(part['functionCall'])
    
    async def handle_audio_response(self, inline_data: dict):
        """
        Convert Gemini audio to Twilio format and send
        """
        try:
            pcm_24k_base64 = inline_data.get('data')
            
            if not pcm_24k_base64:
                return
            
            # Convert: 24kHz PCM → 8kHz μ-law
            mulaw_8k = resampler.gemini_to_twilio(pcm_24k_base64)
            
            # Send back to Twilio
            await self.twilio_ws.send_json({
                "event": "media",
                "streamSid": self.stream_sid,
                "media": {
                    "payload": mulaw_8k
                }
            })
            
        except Exception as e:
            logger.error(f"Error handling audio response: {e}")
    
    async def handle_text_response(self, text: str):
        """
        Log text transcript from Gemini
        Also check for emergency keywords
        """
        self.conversation_transcript.append({
            "role": "assistant",
            "text": text,
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(f" AI: {text}")
        
        # Check for emergency in user's previous speech
        if len(self.conversation_transcript) > 1:
            last_user_text = self.conversation_transcript[-2].get('text', '')
            if self.emergency_handler.detect_emergency(last_user_text):
                logger.warning("⚠️  Emergency keywords detected in conversation")
    
    async def handle_function_call(self, function_call: dict):
        """
        Execute function calls from Gemini
        
        Functions:
        - search_hospitals
        - get_scheme_info
        - get_homework_help
        - call_ambulance
        """
        function_name = function_call.get('name')
        function_id = function_call.get('id')
        args = function_call.get('args', {})
        
        logger.info(f" Function called: {function_name}")
        logger.info(f" Arguments: {args}")
        
        result = None
        
        try:
            # Execute the function
            if function_name == "search_hospitals":
                result = await self.rag_tools.search_hospitals(
                    location=args.get('location', ''),
                    hospital_type=args.get('hospital_type')
                )
                if result.get('success'):
                    self.hospitals_mentioned = result.get('hospitals', [])
            
            elif function_name == "get_scheme_info":
                result = await self.rag_tools.get_scheme_info(
                    query=args.get('query', '')
                )
                if result.get('success'):
                    self.scheme_discussed = True
            
            elif function_name == "get_homework_help":
                result = await self.rag_tools.get_homework_help(
                    subject=args.get('subject'),
                    class_number=args.get('class_number'),
                    question=args.get('question', '')
                )
                if result.get('success'):
                    self.homework_provided = True
            
            elif function_name == "call_ambulance":
                result = await self.emergency_handler.call_ambulance(
                    user_phone=self.user_phone or "Unknown",
                    location=args.get('location', ''),
                    emergency_type=args.get('emergency_type', ''),
                    caller_name=args.get('caller_name'),        # ← from conversation
                    patient_condition=args.get('patient_condition')
                )
                self.emergency_triggered = True
                
                # Send emergency SMS
                if self.user_phone and result.get('success'):
                    await self.sms_service.send_emergency_alert(
                        to_number=self.user_phone,
                        location=args.get('location', ''),
                        emergency_type=args.get('emergency_type', '')
                    )
            
            else:
                logger.warning(f"Unknown function: {function_name}")
                result = {
                    "success": False,
                    "message": f"अज्ञात फंक्शन: {function_name}"
                }
            
            # Send function result back to Gemini
            if result:
                await self.gemini_client.send_function_response(
                    function_call_id=function_id,
                    function_name=function_name,
                    result=result
                )
                
                logger.info(f"Function result sent back to Gemini")
                
        except Exception as e:
            logger.error(f"Error executing function {function_name}: {e}")
            
            # Send error result to Gemini
            await self.gemini_client.send_function_response(
                function_call_id=function_id,
                function_name=function_name,
                result={
                    "success": False,
                    "error": str(e),
                    "message": "फंक्शन निष्पादन में त्रुटि"
                }
            )
    
    async def cleanup(self):
        """Clean up resources when call ends"""
        try:
            if self.gemini_connected:
                await self.gemini_client.close()
                logger.info("Gemini connection closed")
            
            # Log conversation summary
            logger.info(f"Call summary: {len(self.conversation_transcript)} exchanges")
            logger.info(f"Hospitals mentioned: {len(self.hospitals_mentioned)}")
            logger.info(f"Scheme discussed: {self.scheme_discussed}")
            logger.info(f"Homework help: {self.homework_provided}")
            logger.info(f"Emergency: {self.emergency_triggered}")
            
        except Exception as e:
            logger.error(f"Error in cleanup: {e}")