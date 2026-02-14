"""
Audio Resampler Module
Converts between different audio formats:
- Twilio: 8kHz μ-law
- Gemini Input: 16kHz PCM
- Gemini Output: 24kHz PCM
"""
try:
    import audioop
except ImportError:
    import audioop_lts as audioop
import base64
import numpy as np
from scipy import signal
import logging

logger = logging.getLogger(__name__)


class AudioResampler:
    """Handles audio format conversions for streaming voice AI"""
    
    def __init__(self):
        self.twilio_rate = 8000          # Twilio: 8kHz
        self.gemini_input_rate = 16000   # Gemini input: 16kHz
        self.gemini_output_rate = 24000  # Gemini output: 24kHz
        logger.info("AudioResampler initialized")
    
    def twilio_to_gemini(self, mulaw_base64: str) -> str:
        """
        Convert Twilio audio (8kHz μ-law) to Gemini format (16kHz PCM)
        
        Args:
            mulaw_base64: Base64 encoded μ-law audio from Twilio
            
        Returns:
            Base64 encoded 16kHz PCM audio for Gemini
        """
        try:
            # 1. Decode base64
            mulaw_bytes = base64.b64decode(mulaw_base64)
            
            # 2. μ-law to PCM (linear) - 16-bit samples
            pcm_8k = audioop.ulaw2lin(mulaw_bytes, 2)
            
            # 3. Convert to numpy array for resampling
            pcm_8k_array = np.frombuffer(pcm_8k, dtype=np.int16)
            
            # 4. Calculate target number of samples
            num_samples = int(len(pcm_8k_array) * self.gemini_input_rate / self.twilio_rate)
            
            # 5. High-quality resampling using scipy
            pcm_16k_array = signal.resample(pcm_8k_array, num_samples)
            
            # 6. Convert back to int16 bytes
            pcm_16k = pcm_16k_array.astype(np.int16).tobytes()
            
            # 7. Base64 encode for transmission
            return base64.b64encode(pcm_16k).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Error in twilio_to_gemini conversion: {e}")
            raise
    
    def gemini_to_twilio(self, pcm_24k_base64: str) -> str:
        """
        Convert Gemini audio (24kHz PCM) to Twilio format (8kHz μ-law)
        
        Args:
            pcm_24k_base64: Base64 encoded 24kHz PCM from Gemini
            
        Returns:
            Base64 encoded 8kHz μ-law for Twilio
        """
        try:
            # 1. Decode base64
            pcm_24k = base64.b64decode(pcm_24k_base64)
            
            # 2. Convert to numpy array
            pcm_24k_array = np.frombuffer(pcm_24k, dtype=np.int16)
            
            # 3. Calculate target number of samples
            num_samples = int(len(pcm_24k_array) * self.twilio_rate / self.gemini_output_rate)
            
            # 4. Downsample 24kHz → 8kHz
            pcm_8k_array = signal.resample(pcm_24k_array, num_samples)
            
            # 5. Convert back to int16 bytes
            pcm_8k = pcm_8k_array.astype(np.int16).tobytes()
            
            # 6. PCM to μ-law compression
            mulaw_bytes = audioop.lin2ulaw(pcm_8k, 2)
            
            # 7. Base64 encode for transmission
            return base64.b64encode(mulaw_bytes).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Error in gemini_to_twilio conversion: {e}")
            raise
    
    def get_audio_duration(self, audio_bytes: bytes, sample_rate: int) -> float:
        """Calculate audio duration in seconds"""
        num_samples = len(audio_bytes) // 2  # 16-bit = 2 bytes per sample
        return num_samples / sample_rate


# Global instance
resampler = AudioResampler()
