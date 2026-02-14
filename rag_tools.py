"""
RAG Tools Module
Implements function calls for hospital search, scheme info, and homework help
"""

import logging
from typing import Dict, List, Optional
from vector_store import vector_store

logger = logging.getLogger(__name__)


class RAGTools:
    """Tools for RAG-based question answering"""
    
    def __init__(self):
        self.vector_store = vector_store
        logger.info("RAGTools initialized")
    
    async def search_hospitals(
        self, 
        location: str, 
        hospital_type: Optional[str] = None
    ) -> Dict:
        """
        Search for hospitals based on location and type
        
        Args:
            location: City or district name
            hospital_type: Type of hospital (PHC, CHC, District, Private, Any)
            
        Returns:
            Dict with hospital information
        """
        try:
            # Build search query
            if hospital_type and hospital_type != "Any":
                query = f"{hospital_type} hospital in {location}"
            else:
                query = f"hospital in {location}"
            
            logger.info(f"Searching hospitals: {query}")
            
            # Retrieve from vector database
            results = self.vector_store.hospital_db.similarity_search(query, k=3)
            
            if not results:
                return {
                    "success": False,
                    "message": f"{location} में कोई अस्पताल नहीं मिला। कृपया नजदीकी शहर में खोजें।"
                }
            
            # Format results in Hindi
            hospitals_text = f"{location} में निकटतम अस्पताल:\n\n"
            
            hospitals_list = []
            for i, doc in enumerate(results[:3], 1):
                metadata = doc.metadata
                hospital_info = (
                    f"{i}. {metadata.get('name', 'नाम अज्ञात')}\n"
                    f"   फोन: {metadata.get('phone', 'N/A')}\n"
                    f"   पता: {metadata.get('address', 'N/A')}\n"
                    f"   आपातकालीन: {metadata.get('emergency', 'जानकारी उपलब्ध नहीं')}\n"
                )
                hospitals_text += hospital_info + "\n"
                
                hospitals_list.append({
                    "name": metadata.get('name'),
                    "phone": metadata.get('phone'),
                    "address": metadata.get('address'),
                    "type": metadata.get('type'),
                    "emergency": metadata.get('emergency')
                })
            
            hospitals_text += "\nआपातकाल के लिए 108 डायल करें।"
            
            return {
                "success": True,
                "message": hospitals_text,
                "hospitals": hospitals_list,
                "count": len(hospitals_list)
            }
            
        except Exception as e:
            logger.error(f"Error searching hospitals: {e}")
            return {
                "success": False,
                "message": "अस्पताल खोजने में त्रुटि हुई। कृपया फिर से प्रयास करें।",
                "error": str(e)
            }
    
    async def get_scheme_info(self, query: str) -> Dict:
        """
        Get information about Ayushman Bharat scheme
        
        Args:
            query: User's question about the scheme
            
        Returns:
            Dict with scheme information
        """
        try:
            logger.info(f"Querying scheme info: {query}")
            
            # Retrieve relevant information
            results = self.vector_store.scheme_db.similarity_search(query, k=2)
            
            if not results:
                return {
                    "success": False,
                    "message": "योजना की जानकारी नहीं मिली। कृपया 14555 पर कॉल करें।"
                }
            
            # Combine relevant context
            context = "\n\n".join([doc.page_content for doc in results])
            
            # Add helpline info
            context += "\n\nअधिक जानकारी के लिए:\n📞 टोल-फ्री: 14555\n🌐 वेबसाइट: pmjay.gov.in"
            
            return {
                "success": True,
                "message": context,
                "helpline": "14555",
                "website": "pmjay.gov.in"
            }
            
        except Exception as e:
            logger.error(f"Error getting scheme info: {e}")
            return {
                "success": False,
                "message": "योजना की जानकारी लाने में त्रुटि। कृपया 14555 पर संपर्क करें।",
                "error": str(e)
            }
    
    async def get_homework_help(
        self, 
        subject: Optional[str],
        class_number: Optional[int],
        question: str
    ) -> Dict:
        """
        Help with homework questions based on NCERT curriculum
        
        Args:
            subject: Subject name (science, maths, social_studies, etc.)
            class_number: Class number (6-12)
            question: Student's question
            
        Returns:
            Dict with answer/explanation
        """
        try:
            # Build search query
            search_parts = []
            if class_number:
                search_parts.append(f"कक्षा {class_number}")
            if subject:
                subject_hindi = {
                    "science": "विज्ञान",
                    "maths": "गणित",
                    "social_studies": "सामाजिक विज्ञान",
                    "hindi": "हिंदी",
                    "english": "अंग्रेजी"
                }.get(subject, subject)
                search_parts.append(subject_hindi)
            search_parts.append(question)
            
            search_query = " ".join(search_parts)
            logger.info(f"Homework help query: {search_query}")
            
            # Retrieve relevant content
            results = self.vector_store.ncert_db.similarity_search(search_query, k=2)
            
            if not results:
                return {
                    "success": False,
                    "message": "इस सवाल का जवाब नहीं मिला। कृपया अपने शिक्षक से पूछें।"
                }
            
            # Combine context
            context = "\n\n".join([doc.page_content for doc in results])
            
            # Add study tip
            context += "\n\n💡 सुझाव: अपनी NCERT किताब का संबंधित अध्याय भी पढ़ें।"
            
            return {
                "success": True,
                "message": context,
                "subject": subject,
                "class": class_number
            }
            
        except Exception as e:
            logger.error(f"Error getting homework help: {e}")
            return {
                "success": False,
                "message": "होमवर्क में मदद करने में त्रुटि। कृपया फिर से प्रयास करें।",
                "error": str(e)
            }


# Global instance
rag_tools = RAGTools()
