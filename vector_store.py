"""
Vector Store Module
Manages FAISS vector databases for RAG (Retrieval Augmented Generation)
"""

import os
import pickle
import logging
from typing import List, Dict
from pathlib import Path

import numpy as np


from langchain_core.documents import Document

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """Manages multiple FAISS vector stores for different knowledge bases"""
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        
        # Store instances
        self.hospital_db = None
        self.scheme_db = None
        self.ncert_db = None
        
        logger.info("VectorStoreManager initialized")
    
    def create_hospital_db(self):
        """Create vector database for hospital information"""
        hospital_data = [
            {
                "name": "गुवाहाटी मेडिकल कॉलेज और अस्पताल",
                "type": "Government Medical College",
                "phone": "0361-2528056",
                "address": "भंगागढ़, गुवाहाटी, असम 781032",
                "location": "गुवाहाटी",
                "district": "कामरूप",
                "state": "असम",
                "emergency": "24x7 आपातकालीन सेवा उपलब्ध",
                "specialties": "सामान्य चिकित्सा, सर्जरी, बाल रोग, प्रसूति"
            },
            {
                "name": "महात्मा गांधी मेमोरियल अस्पताल",
                "type": "District Hospital",
                "phone": "0361-2540625",
                "address": "बेलतोला, गुवाहाटी, असम 781028",
                "location": "गुवाहाटी",
                "district": "कामरूप",
                "state": "असम",
                "emergency": "24 घंटे उपलब्ध",
                "specialties": "आपातकालीन देखभाल, सामान्य चिकित्सा"
            },
            {
                "name": "नेमकेयर अस्पताल",
                "type": "Private",
                "phone": "0361-2237797",
                "address": "भांगागढ़, गुवाहाटी, असम 781005",
                "location": "गुवाहाटी",
                "district": "कामरूप",
                "state": "असम",
                "emergency": "24x7 एम्बुलेंस सेवा",
                "specialties": "हृदय रोग, न्यूरोलॉजी, ऑर्थोपेडिक्स"
            },
            {
                "name": "डाउन टाउन अस्पताल",
                "type": "Private",
                "phone": "0361-2331002",
                "address": "डिसपुर, गुवाहाटी, असम 781006",
                "location": "गुवाहाटी",
                "district": "कामरूप",
                "state": "असम",
                "emergency": "आपातकालीन विभाग 24x7",
                "specialties": "कैंसर देखभाल, न्यूरोसर्जरी, ट्रॉमा केयर"
            },
            {
                "name": "प्राथमिक स्वास्थ्य केंद्र (PHC) बेलतोला",
                "type": "PHC",
                "phone": "0361-2540000",
                "address": "बेलतोला, गुवाहाटी, असम",
                "location": "गुवाहाटी",
                "district": "कामरूप",
                "state": "असम",
                "emergency": "दिन में उपलब्ध",
                "specialties": "सामान्य चिकित्सा, टीकाकरण"
            }
        ]
        
        documents = []
        for hospital in hospital_data:
            content = f"""
            अस्पताल: {hospital['name']}
            प्रकार: {hospital['type']}
            फोन: {hospital['phone']}
            पता: {hospital['address']}
            स्थान: {hospital['location']}, {hospital['district']}, {hospital['state']}
            आपातकालीन सेवा: {hospital['emergency']}
            विशेषताएं: {hospital['specialties']}
            """
            
            doc = Document(
                page_content=content.strip(),
                metadata=hospital
            )
            documents.append(doc)
        
        self.hospital_db = FAISS.from_documents(documents, self.embeddings)
        
        # Save to disk
        save_path = self.data_dir / "hospital_vectors"
        save_path.mkdir(parents=True, exist_ok=True)
        self.hospital_db.save_local(str(save_path))
        
        logger.info(f"Hospital database created with {len(documents)} entries")
        return self.hospital_db
    
    def create_scheme_db(self):
        """Create vector database for Ayushman Bharat scheme information"""
        scheme_data = [
            """
            आयुष्मान भारत योजना - मुख्य जानकारी:
            
            यह भारत सरकार की एक स्वास्थ्य बीमा योजना है जो गरीब और कमजोर परिवारों को मुफ्त इलाज की सुविधा देती है।
            
            लाभ:
            - प्रति परिवार प्रति वर्ष 5 लाख रुपये तक का मुफ्त इलाज
            - 1,900+ बीमारियों और प्रक्रियाओं का कवरेज
            - अस्पताल में भर्ती से 3 दिन पहले और 15 दिन बाद तक का खर्च
            - देश भर के सूचीबद्ध अस्पतालों में उपलब्ध
            
            पात्रता:
            - गरीबी रेखा से नीचे (BPL) परिवार
            - SECC 2011 डेटाबेस में शामिल परिवार
            - कच्चे घर वाले परिवार
            - दिव्यांग सदस्य वाले परिवार
            - भूमिहीन मजदूर
            """,
            """
            आयुष्मान भारत कार्ड कैसे बनाएं:
            
            कदम 1: नजदीकी आयुष्मान मित्र केंद्र या सूचीबद्ध अस्पताल जाएं
            कदम 2: राशन कार्ड, आधार कार्ड, और परिवार पहचान पत्र ले जाएं
            कदम 3: अपनी पात्रता जांचें (मोबाइल नंबर से OTP आएगा)
            कदम 4: तस्वीर खींचवाएं और बायोमेट्रिक दें
            कदम 5: तुरंत गोल्डन कार्ड प्राप्त करें
            
            हेल्पलाइन: 14555 (टोल फ्री)
            वेबसाइट: pmjay.gov.in
            
            नोट: कार्ड बनाना और इस्तेमाल करना पूरी तरह मुफ्त है। कोई भी पैसे मांगे तो शिकायत करें।
            """,
            """
            किन बीमारियों का इलाज होता है:
            
            सर्जरी:
            - कैंसर की सर्जरी
            - हृदय रोग (बाईपास, एंजियोप्लास्टी)
            - घुटना/कूल्हा बदलना
            - मोतियाबिंद ऑपरेशन
            
            आपातकालीन:
            - दुर्घटना में चोट
            - जलने का इलाज
            - सांप काटने पर उपचार
            
            गंभीर बीमारियां:
            - डायलिसिस (किडनी खराब होने पर)
            - कीमोथेरेपी/रेडिएशन
            - न्यूरोसर्जरी
            - प्रसव और सी-सेक्शन
            
            शामिल नहीं:
            - कॉस्मेटिक सर्जरी
            - ड्रग रिहैबिलिटेशन
            - OPD (बाहरी मरीज) इलाज
            """,
            """
            अस्पताल में भर्ती कैसे हों:
            
            1. आयुष्मान कार्ड और आधार कार्ड लेकर जाएं
            2. अस्पताल के आयुष्मान डेस्क पर जाएं
            3. अपना कार्ड दिखाएं - कोई पैसा जमा नहीं करना होगा
            4. इलाज पूरी तरह कैशलेस होगा
            5. दवाइयां, जांच, बेड, डॉक्टर फीस - सब फ्री
            
            असम में 500+ अस्पताल इस योजना में शामिल हैं।
            
            अपने नजदीकी अस्पताल खोजने के लिए:
            - 14555 पर कॉल करें
            - mera.pmjay.gov.in पर देखें
            - आयुष्मान भारत ऐप डाउनलोड करें
            """
        ]
        
        documents = [Document(page_content=text.strip()) for text in scheme_data]
        
        self.scheme_db = FAISS.from_documents(documents, self.embeddings)
        
        # Save to disk
        save_path = self.data_dir / "scheme_vectors"
        save_path.mkdir(parents=True, exist_ok=True)
        self.scheme_db.save_local(str(save_path))
        
        logger.info(f"Scheme database created with {len(documents)} entries")
        return self.scheme_db
    
    def create_ncert_db(self):
        """Create vector database for NCERT homework help"""
        ncert_data = [
            """
            कक्षा 8 विज्ञान: फसल उत्पादन और प्रबंधन
            
            फसल: पौधों की वह खेती जो एक ही प्रकार के बड़े पैमाने पर उगाई जाती है।
            
            फसल के प्रकार:
            1. खरीफ फसल - जून-जुलाई में बुवाई, सितंबर-अक्टूबर में कटाई (धान, मक्का, कपास)
            2. रबी फसल - अक्टूबर-नवंबर में बुवाई, मार्च-अप्रैल में कटाई (गेहूं, चना, सरसों)
            
            मृदा की तैयारी: हल चलाना (जुताई) → समतल करना → खाद मिलाना
            
            खाद और उर्वरक:
            - खाद: जैविक पदार्थ (गोबर की खाद, कम्पोस्ट)
            - उर्वरक: रासायनिक पदार्थ (यूरिया, DAP)
            
            सिंचाई के तरीके: नहर, कुआं, ट्यूबवेल, स्प्रिंकलर, ड्रिप
            """,
            """
            कक्षा 9 गणित: बीजगणित
            
            बहुपद (Polynomial): चर और अचर राशियों का योगफल
            उदाहरण: 3x² + 2x + 5
            
            बहुपद की घात: चर की सबसे बड़ी घात
            - रैखिक बहुपद: घात 1 (2x + 3)
            - द्विघात बहुपद: घात 2 (x² + 5x + 6)
            - त्रिघात बहुपद: घात 3 (x³ + 2x² + x + 1)
            
            शून्यक: वह मान जिस पर बहुपद का मान शून्य हो
            
            गुणनखंड: बहुपद को छोटे गुणनखंडों में तोड़ना
            उदाहरण: x² + 5x + 6 = (x + 2)(x + 3)
            """,
            """
            कक्षा 10 विज्ञान: रासायनिक अभिक्रियाएं
            
            रासायनिक अभिक्रिया: पदार्थों का रासायनिक परिवर्तन जिससे नए पदार्थ बनते हैं।
            
            प्रकार:
            1. संयोजन: A + B → AB (कैल्शियम + ऑक्सीजन → कैल्शियम ऑक्साइड)
            2. वियोजन: AB → A + B (जल → हाइड्रोजन + ऑक्सीजन)
            3. विस्थापन: A + BC → AC + B (लोहा + कॉपर सल्फेट)
            4. द्विविस्थापन: AB + CD → AD + CB
            
            ऊष्माक्षेपी: ऊष्मा निकलती है (जलना)
            ऊष्माशोषी: ऊष्मा अवशोषित होती है (प्रकाश संश्लेषण)
            
            रासायनिक समीकरण को संतुलित करना:
            - दोनों तरफ परमाणुओं की संख्या बराबर होनी चाहिए
            """,
            """
            कक्षा 7 सामाजिक विज्ञान: मुगल साम्राज्य
            
            प्रमुख शासक:
            1. बाबर (1526-1530): पानीपत की पहली लड़ाई
            2. अकबर (1556-1605): धार्मिक सहिष्णुता, दीन-ए-इलाही
            3. जहांगीर (1605-1627): न्याय की जंजीर
            4. शाहजहां (1628-1658): ताजमहल का निर्माण
            5. औरंगजेब (1658-1707): अंतिम महान मुगल शासक
            
            प्रशासनिक व्यवस्था:
            - मनसबदारी प्रथा: सैनिक और प्रशासनिक पद
            - जागीर: भूमि अनुदान
            - सूबा: प्रांत, सूबेदार द्वारा शासित
            
            कला और संस्कृति:
            - वास्तुकला: ताजमहल, लाल किला, फतेहपुर सीकरी
            - चित्रकला: मुगल लघु चित्र
            - साहित्य: फारसी और हिंदी का विकास
            """
        ]
        
        documents = [Document(page_content=text.strip()) for text in ncert_data]
        
        self.ncert_db = FAISS.from_documents(documents, self.embeddings)
        
        # Save to disk
        save_path = self.data_dir / "ncert_vectors"
        save_path.mkdir(parents=True, exist_ok=True)
        self.ncert_db.save_local(str(save_path))
        
        logger.info(f"NCERT database created with {len(documents)} entries")
        return self.ncert_db
    
    def load_all_databases(self):
        """Load all vector databases from disk"""
        try:
            hospital_path = self.data_dir / "hospital_vectors"
            if hospital_path.exists():
                self.hospital_db = FAISS.load_local(
                    str(hospital_path),
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                logger.info("Hospital database loaded")
            else:
                logger.warning("Hospital database not found, creating new one")
                self.create_hospital_db()
            
            scheme_path = self.data_dir / "scheme_vectors"
            if scheme_path.exists():
                self.scheme_db = FAISS.load_local(
                    str(scheme_path),
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                logger.info("Scheme database loaded")
            else:
                logger.warning("Scheme database not found, creating new one")
                self.create_scheme_db()
            
            ncert_path = self.data_dir / "ncert_vectors"
            if ncert_path.exists():
                self.ncert_db = FAISS.load_local(
                    str(ncert_path),
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                logger.info("NCERT database loaded")
            else:
                logger.warning("NCERT database not found, creating new one")
                self.create_ncert_db()
                
        except Exception as e:
            logger.error(f"Error loading databases: {e}")
            raise
    
    def create_all_databases(self):
        """Create all databases from scratch"""
        self.create_hospital_db()
        self.create_scheme_db()
        self.create_ncert_db()
        logger.info("All databases created successfully")


# Global instance
vector_store = VectorStoreManager()
