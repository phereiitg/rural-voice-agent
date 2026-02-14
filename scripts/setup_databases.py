"""
Database Setup Script
Creates and initializes all FAISS vector databases
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from vector_store import vector_store

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Create all vector databases"""
    logger.info("🚀 Starting database creation...")
    
    try:
        # Create hospital database
        logger.info("Creating hospital database...")
        vector_store.create_hospital_db()
        logger.info("✅ Hospital database created")
        
        # Create scheme database
        logger.info("Creating Ayushman Bharat scheme database...")
        vector_store.create_scheme_db()
        logger.info("✅ Scheme database created")
        
        # Create NCERT database
        logger.info("Creating NCERT homework database...")
        vector_store.create_ncert_db()
        logger.info("✅ NCERT database created")
        
        logger.info("🎉 All databases created successfully!")
        logger.info(f"📁 Databases saved in: {vector_store.data_dir}")
        
        # Test loading
        logger.info("Testing database loading...")
        vector_store.load_all_databases()
        logger.info("✅ All databases loaded successfully")
        
        # Print statistics
        logger.info("\n📊 Database Statistics:")
        logger.info(f"Hospital entries: {vector_store.hospital_db.index.ntotal if vector_store.hospital_db else 0}")
        logger.info(f"Scheme entries: {vector_store.scheme_db.index.ntotal if vector_store.scheme_db else 0}")
        logger.info(f"NCERT entries: {vector_store.ncert_db.index.ntotal if vector_store.ncert_db else 0}")
        
    except Exception as e:
        logger.error(f"❌ Error creating databases: {e}")
        raise


if __name__ == "__main__":
    main()
