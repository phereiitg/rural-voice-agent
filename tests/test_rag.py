"""
Test Script for RAG Functions
Tests hospital search, scheme info, and homework help
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag_tools import rag_tools
from vector_store import vector_store

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_hospital_search():
    """Test hospital search function"""
    logger.info("\n" + "="*50)
    logger.info("🏥 Testing Hospital Search")
    logger.info("="*50)
    
    # Test 1: Search in Guwahati
    result = await rag_tools.search_hospitals("गुवाहाटी")
    print(f"\nResult 1 - Guwahati hospitals:")
    print(f"Success: {result['success']}")
    print(f"Message:\n{result['message']}")
    
    # Test 2: Search for specific type
    result = await rag_tools.search_hospitals("गुवाहाटी", "Private")
    print(f"\nResult 2 - Private hospitals in Guwahati:")
    print(f"Message:\n{result['message']}")
    
    # Test 3: Search in unknown location
    result = await rag_tools.search_hospitals("दिल्ली")
    print(f"\nResult 3 - Delhi (should have limited results):")
    print(f"Message:\n{result['message']}")


async def test_scheme_info():
    """Test Ayushman Bharat scheme info"""
    logger.info("\n" + "="*50)
    logger.info("💊 Testing Scheme Information")
    logger.info("="*50)
    
    # Test 1: General info
    result = await rag_tools.get_scheme_info("आयुष्मान भारत क्या है?")
    print(f"\nResult 1 - What is Ayushman Bharat:")
    print(f"Success: {result['success']}")
    print(f"Message:\n{result['message'][:500]}...")
    
    # Test 2: Eligibility
    result = await rag_tools.get_scheme_info("कौन पात्र है?")
    print(f"\nResult 2 - Eligibility:")
    print(f"Message:\n{result['message'][:500]}...")
    
    # Test 3: How to apply
    result = await rag_tools.get_scheme_info("कार्ड कैसे बनाएं?")
    print(f"\nResult 3 - How to get card:")
    print(f"Message:\n{result['message'][:500]}...")


async def test_homework_help():
    """Test NCERT homework help"""
    logger.info("\n" + "="*50)
    logger.info("📚 Testing Homework Help")
    logger.info("="*50)
    
    # Test 1: Science question
    result = await rag_tools.get_homework_help(
        subject="science",
        class_number=8,
        question="फसल उत्पादन क्या है?"
    )
    print(f"\nResult 1 - Class 8 Science:")
    print(f"Success: {result['success']}")
    print(f"Message:\n{result['message'][:500]}...")
    
    # Test 2: Maths question
    result = await rag_tools.get_homework_help(
        subject="maths",
        class_number=9,
        question="बहुपद क्या होता है?"
    )
    print(f"\nResult 2 - Class 9 Maths:")
    print(f"Message:\n{result['message'][:500]}...")
    
    # Test 3: General question
    result = await rag_tools.get_homework_help(
        subject=None,
        class_number=None,
        question="रासायनिक अभिक्रिया के प्रकार"
    )
    print(f"\nResult 3 - General chemistry:")
    print(f"Message:\n{result['message'][:500]}...")


async def main():
    """Run all tests"""
    logger.info("🚀 Starting RAG Function Tests\n")
    
    # Load databases
    logger.info("Loading vector databases...")
    try:
        vector_store.load_all_databases()
        logger.info("✅ Databases loaded successfully\n")
    except Exception as e:
        logger.error(f"❌ Error loading databases: {e}")
        logger.info("Please run: python scripts/setup_databases.py")
        return
    
    # Run tests
    await test_hospital_search()
    await test_scheme_info()
    await test_homework_help()
    
    logger.info("\n" + "="*50)
    logger.info("✅ All tests completed!")
    logger.info("="*50)


if __name__ == "__main__":
    asyncio.run(main())
