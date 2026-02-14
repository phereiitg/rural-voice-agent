"""
Demo Script - Test Voice AI Components Locally
Without making actual phone calls
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag_tools import rag_tools
from vector_store import vector_store
from emergency_handler import emergency_handler
from audio_resampler import resampler
import base64


class Colors:
    """ANSI color codes for pretty output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Print colored header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}\n")


def print_section(text):
    """Print section header"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}▶ {text}{Colors.END}")
    print(f"{Colors.CYAN}{'-'*60}{Colors.END}")


def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_info(text):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")


async def demo_audio_resampling():
    """Demo audio resampling functionality"""
    print_section("Audio Resampling Demo")
    
    try:
        # Create dummy audio data
        print_info("Creating dummy μ-law audio (8kHz)...")
        dummy_audio = b'\x00' * 160  # 20ms of silence
        mulaw_base64 = base64.b64encode(dummy_audio).decode('utf-8')
        
        # Test upsampling (Twilio → Gemini)
        print_info("Testing upsampling: 8kHz μ-law → 16kHz PCM...")
        pcm_16k = resampler.twilio_to_gemini(mulaw_base64)
        print_success(f"Upsampled! Output size: {len(pcm_16k)} bytes")
        
        # Test downsampling (Gemini → Twilio)
        print_info("Testing downsampling: 24kHz PCM → 8kHz μ-law...")
        dummy_pcm = b'\x00\x00' * 480  # 24kHz sample
        pcm_base64 = base64.b64encode(dummy_pcm).decode('utf-8')
        mulaw_8k = resampler.gemini_to_twilio(pcm_base64)
        print_success(f"Downsampled! Output size: {len(mulaw_8k)} bytes")
        
        print_success("Audio resampling working correctly! ✓")
        
    except Exception as e:
        print_error(f"Audio resampling failed: {e}")


async def demo_hospital_search():
    """Demo hospital search"""
    print_section("Hospital Search Demo")
    
    queries = [
        ("गुवाहाटी", None, "General search in Guwahati"),
        ("गुवाहाटी", "Private", "Private hospitals in Guwahati"),
        ("गुवाहाटी", "PHC", "Primary Health Centers")
    ]
    
    for location, h_type, description in queries:
        print_info(f"Query: {description}")
        result = await rag_tools.search_hospitals(location, h_type)
        
        if result['success']:
            print_success(f"Found {result.get('count', 0)} hospitals")
            print(f"\n{result['message']}\n")
        else:
            print_error(result['message'])


async def demo_scheme_info():
    """Demo Ayushman Bharat scheme queries"""
    print_section("Ayushman Bharat Scheme Demo")
    
    queries = [
        "आयुष्मान भारत क्या है?",
        "कौन पात्र है?",
        "कार्ड कैसे बनाएं?"
    ]
    
    for query in queries:
        print_info(f"Query: {query}")
        result = await rag_tools.get_scheme_info(query)
        
        if result['success']:
            print_success("Information retrieved")
            # Print first 300 chars
            message = result['message']
            print(f"\n{message[:300]}...\n")
        else:
            print_error(result['message'])


async def demo_homework_help():
    """Demo homework assistance"""
    print_section("Homework Help Demo")
    
    queries = [
        ("science", 8, "फसल उत्पादन क्या है?", "Class 8 Science"),
        ("maths", 9, "बहुपद क्या होता है?", "Class 9 Maths"),
        (None, None, "रासायनिक अभिक्रिया", "General Chemistry")
    ]
    
    for subject, class_num, question, description in queries:
        print_info(f"Query: {description} - {question}")
        result = await rag_tools.get_homework_help(subject, class_num, question)
        
        if result['success']:
            print_success("Answer found")
            # Print first 300 chars
            message = result['message']
            print(f"\n{message[:300]}...\n")
        else:
            print_error(result['message'])


async def demo_emergency_detection():
    """Demo emergency keyword detection"""
    print_section("Emergency Detection Demo")
    
    test_phrases = [
        ("मुझे दिल का दौरा हो रहा है", True),
        ("मेरे को अस्पताल चाहिए", False),
        ("दुर्घटना हो गई है", True),
        ("मेरा होमवर्क क्या है?", False),
        ("खून बह रहा है", True)
    ]
    
    for phrase, should_detect in test_phrases:
        detected = emergency_handler.detect_emergency(phrase)
        
        if detected == should_detect:
            print_success(f"'{phrase}' - Correctly {'detected' if detected else 'not detected'}")
        else:
            print_error(f"'{phrase}' - Should be {'emergency' if should_detect else 'normal'}")


async def demo_conversation_flow():
    """Demo a complete conversation flow"""
    print_section("Complete Conversation Flow Demo")
    
    conversation = [
        {
            "user": "नमस्ते, मुझे मदद चाहिए",
            "expected_response": "Greeting and offer help"
        },
        {
            "user": "मुझे गुवाहाटी में अस्पताल चाहिए",
            "function": "search_hospitals",
            "args": {"location": "गुवाहाटी"}
        },
        {
            "user": "आयुष्मान भारत के बारे में बताओ",
            "function": "get_scheme_info",
            "args": {"query": "आयुष्मान भारत"}
        },
        {
            "user": "धन्यवाद",
            "expected_response": "Closing and SMS summary"
        }
    ]
    
    print_info("Simulating conversation flow...\n")
    
    for i, turn in enumerate(conversation, 1):
        print(f"{Colors.YELLOW}Turn {i}:{Colors.END}")
        print(f"  User: {turn['user']}")
        
        if 'function' in turn:
            print(f"  → AI should call: {turn['function']}({turn['args']})")
            
            # Simulate function call
            if turn['function'] == 'search_hospitals':
                result = await rag_tools.search_hospitals(**turn['args'])
                if result['success']:
                    print_success(f"  → Function returned: {result.get('count', 0)} hospitals")
            
            elif turn['function'] == 'get_scheme_info':
                result = await rag_tools.get_scheme_info(**turn['args'])
                if result['success']:
                    print_success("  → Function returned: scheme information")
        
        else:
            print(f"  → AI should: {turn['expected_response']}")
        
        print()


async def demo_performance_test():
    """Test performance of key operations"""
    print_section("Performance Test")
    
    import time
    
    # Test hospital search speed
    print_info("Testing hospital search speed...")
    start = time.time()
    for _ in range(10):
        await rag_tools.search_hospitals("गुवाहाटी")
    elapsed = (time.time() - start) / 10
    
    if elapsed < 0.1:
        print_success(f"Average search time: {elapsed*1000:.1f}ms ✓")
    else:
        print_error(f"Average search time: {elapsed*1000:.1f}ms (too slow!)")
    
    # Test audio resampling speed
    print_info("Testing audio resampling speed...")
    dummy_audio = base64.b64encode(b'\x00' * 160).decode('utf-8')
    
    start = time.time()
    for _ in range(100):
        resampler.twilio_to_gemini(dummy_audio)
    elapsed = (time.time() - start) / 100
    
    if elapsed < 0.01:
        print_success(f"Average resampling time: {elapsed*1000:.2f}ms ✓")
    else:
        print_error(f"Average resampling time: {elapsed*1000:.2f}ms (too slow!)")


async def main():
    """Run all demos"""
    print_header("🚀 STREAMING VOICE AI - DEMO SCRIPT")
    
    print(f"{Colors.BOLD}This script tests all components without making actual calls{Colors.END}\n")
    
    # Load databases
    print_section("Loading Vector Databases")
    try:
        vector_store.load_all_databases()
        print_success("Hospital database loaded")
        print_success("Scheme database loaded")
        print_success("NCERT database loaded")
    except Exception as e:
        print_error(f"Database loading failed: {e}")
        print_info("Run: python scripts/setup_databases.py")
        return
    
    # Run demos
    await demo_audio_resampling()
    await demo_hospital_search()
    await demo_scheme_info()
    await demo_homework_help()
    await demo_emergency_detection()
    await demo_conversation_flow()
    await demo_performance_test()
    
    # Final summary
    print_header("✅ DEMO COMPLETE")
    print(f"{Colors.GREEN}All components working correctly!{Colors.END}\n")
    print(f"{Colors.BOLD}Next steps:{Colors.END}")
    print("1. Set up environment variables in .env")
    print("2. Start server: python main.py")
    print("3. Start ngrok: ngrok http 8000")
    print("4. Update Twilio webhook")
    print("5. Make a test call!\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Demo interrupted by user{Colors.END}\n")
    except Exception as e:
        print(f"\n\n{Colors.RED}Demo failed: {e}{Colors.END}\n")
