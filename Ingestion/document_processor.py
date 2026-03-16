import io
import logging
from pathlib import Path
from typing import Optional
import pypdf
# import docx
import markdown
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Parse différents types de documents en texte brut"""
    
    @staticmethod
    def parse_pdf(file_content: bytes) -> str:
        """Extrait le texte d'un PDF"""
        try:
            pdf_file = io.BytesIO(file_content)
            reader = pypdf.PdfReader(pdf_file)
            text = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
            return "\n".join(text)
        except Exception as e:
            logger.error(f"Erreur parsing PDF: {e}")
            return ""
    
    @staticmethod
    def parse_docx(file_content: bytes) -> str:
        """Extrait le texte d'un DOCX"""
        try:
            docx_file = io.BytesIO(file_content)
            # doc = docx.Document(docx_file)
            doc = ""
            text = [para.text for para in doc.paragraphs]
            return "\n".join(text)
        except Exception as e:
            logger.error(f"Erreur parsing DOCX: {e}")
            return ""
    
    @staticmethod
    def parse_markdown(file_content: bytes) -> str:
        """Convertit le Markdown en texte brut"""
        try:
            md_text = file_content.decode('utf-8')
            html = markdown.markdown(md_text)
            soup = BeautifulSoup(html, 'html.parser')
            return soup.get_text()
        except Exception as e:
            logger.error(f"Erreur parsing Markdown: {e}")
            return ""
    
    @staticmethod
    def parse_txt(file_content: bytes) -> str:
        """Lit un fichier texte"""
        try:
            return file_content.decode('utf-8')
        except UnicodeDecodeError:
            # Essayer d'autres encodages
            try:
                return file_content.decode('latin-1')
            except Exception as e:
                logger.error(f"Erreur parsing TXT: {e}")
                return ""
    
    def process(self, file_content: bytes, filename: str) -> Optional[str]:
        """
        Traite un document selon son extension
        
        Args:
            file_content: Contenu binaire du fichier
            filename: Nom du fichier (pour déterminer le type)
            
        Returns:
            Texte extrait ou None si erreur
        """
        ext = Path(filename).suffix.lower()
        
        processors = {
            '.pdf': self.parse_pdf,
            '.docx': self.parse_docx,
            '.doc': self.parse_docx,  # .doc non supporté directement
            '.md': self.parse_markdown,
            '.markdown': self.parse_markdown,
            '.txt': self.parse_txt,
            '.csv': self.parse_txt,
            '.json': self.parse_txt,
        }
        
        processor = processors.get(ext)
        if not processor:
            logger.warning(f"Extension non supportée: {ext}")
            return None
        
        try:
            text = processor(file_content)
            if text and len(text.strip()) > 0:
                logger.info(f"✅ Document traité: {filename} ({len(text)} caractères)")
                return text
            else:
                logger.warning(f"⚠️ Document vide: {filename}")
                return None
        except Exception as e:
            logger.error(f"❌ Erreur traitement {filename}: {e}")
            return None