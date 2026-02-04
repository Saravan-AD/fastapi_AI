import os
from pypdf import PdfReader
import re
import tiktoken
from typing import List, Dict, Any

DOCS_PATH = "documents"

class ImprovedChunker:
    def __init__(self, max_tokens=500, overlap_tokens=50):
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
    def count_tokens(self, text: str) -> int:
        """Count tokens (not characters)"""
        return len(self.tokenizer.encode(text))
    
    def split_into_sentences(self, text: str) -> List[str]:
        """Simple sentence splitting without nltk"""
        # Split by . ! ? followed by space or newline
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def smart_chunk(self, text: str, metadata: Dict = None) -> List[Dict[str, Any]]:
        """
        Improved chunking with token counting and better paragraph handling
        """
        if metadata is None:
            metadata = {}
        
        chunks = []
        
        # 1. Split by paragraphs (double newlines)
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
        
        current_chunk = ""
        current_tokens = 0
        
        for para in paragraphs:
            para_tokens = self.count_tokens(para)
            
            # If paragraph is huge, split by sentences
            if para_tokens > self.max_tokens:
                sentences = self.split_into_sentences(para)
                
                for sentence in sentences:
                    sent_tokens = self.count_tokens(sentence)
                    
                    # If sentence itself is too big (rare), split by words
                    if sent_tokens > self.max_tokens:
                        words = sentence.split()
                        temp_chunk = ""
                        temp_tokens = 0
                        
                        for word in words:
                            word_tokens = self.count_tokens(word + " ")
                            
                            if temp_tokens + word_tokens > self.max_tokens:
                                chunks.append(self._create_chunk(
                                    temp_chunk, metadata, len(chunks)
                                ))
                                temp_chunk = word
                                temp_tokens = word_tokens
                            else:
                                temp_chunk += " " + word
                                temp_tokens += word_tokens
                        
                        if temp_chunk:
                            if current_tokens + temp_tokens > self.max_tokens:
                                if current_chunk:
                                    chunks.append(self._create_chunk(
                                        current_chunk, metadata, len(chunks)
                                    ))
                                current_chunk = temp_chunk
                                current_tokens = temp_tokens
                            else:
                                current_chunk += " " + temp_chunk
                                current_tokens += temp_tokens
                    
                    # Normal sentence handling
                    elif current_tokens + sent_tokens > self.max_tokens:
                        if current_chunk:
                            chunks.append(self._create_chunk(
                                current_chunk, metadata, len(chunks)
                            ))
                        
                        # Start new chunk with this sentence
                        current_chunk = sentence
                        current_tokens = sent_tokens
                    else:
                        current_chunk += " " + sentence
                        current_tokens += sent_tokens
            
            # Normal paragraph (fits in chunk)
            elif current_tokens + para_tokens > self.max_tokens:
                if current_chunk:
                    chunks.append(self._create_chunk(
                        current_chunk, metadata, len(chunks)
                    ))
                
                # Start new chunk with this paragraph
                current_chunk = para
                current_tokens = para_tokens
            else:
                current_chunk += " " + para
                current_tokens += para_tokens
        
        # Add the last chunk
        if current_chunk:
            chunks.append(self._create_chunk(
                current_chunk, metadata, len(chunks)
            ))
        
        # Apply intelligent overlap
        return self._apply_overlap(chunks)
    
    def _create_chunk(self, text: str, metadata: Dict, chunk_id: int) -> Dict:
        """Create a chunk with metadata"""
        return {
            'text': text.strip(),
            'metadata': {
                **metadata,
                'chunk_id': chunk_id,
                'tokens': self.count_tokens(text),
                'characters': len(text)
            }
        }
    
    def _apply_overlap(self, chunks: List[Dict]) -> List[Dict]:
        """Apply overlap without duplication"""
        if len(chunks) <= 1:
            return chunks
        
        overlapped_chunks = [chunks[0]]  # First chunk stays as is
        
        for i in range(1, len(chunks)):
            prev_text = chunks[i-1]['text']
            curr_text = chunks[i]['text']
            
            # Get tokens from previous chunk for overlap
            prev_tokens = self.tokenizer.encode(prev_text)
            
            # Take last 'overlap_tokens' tokens from previous chunk
            overlap_start = max(0, len(prev_tokens) - self.overlap_tokens)
            overlap_tokens = prev_tokens[overlap_start:]
            
            # Convert back to text
            overlap_text = self.tokenizer.decode(overlap_tokens)
            
            # Combine with current chunk
            combined_text = overlap_text + " " + curr_text
            
            # Create new chunk with overlap
            overlapped_chunks.append({
                'text': combined_text.strip(),
                'metadata': {
                    **chunks[i]['metadata'],
                    'has_overlap': True,
                    'overlap_tokens': len(overlap_tokens)
                }
            })
        
        return overlapped_chunks

def find_relevant_chunks(question, chunks, top_k=3):
    """
    FIXED VERSION: Handles both dict and string chunks
    """
    # 1. Clean and prepare question words
    question_lower = question.lower()
    
    # Common words to ignore
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
        'for', 'of', 'with', 'by', 'as', 'is', 'are', 'was', 'were',
        'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
        'did', 'will', 'would', 'shall', 'should', 'may', 'might',
        'must', 'can', 'could', 'i', 'you', 'we', 'they', 'he', 'she',
        'it', 'my', 'your', 'our', 'their', 'this', 'that', 'these',
        'those', 'what', 'which', 'who', 'whom', 'whose', 'how', 'why',
        'when', 'where'
    }
    
    # Get important words from question
    question_words = []
    for word in question_lower.split():
        word = word.strip('.,!?;:"\'()[]{}')
        if word and word not in stop_words and len(word) > 2:
            question_words.append(word)
    
    if not question_words:
        question_words = [w.strip('.,!?;:"\'()[]{}') 
                         for w in question_lower.split() if w]
    
    # 2. Score each chunk
    scored_chunks = []
    
    for chunk in chunks:
        # 🔧 FIX HERE: Extract text from dict OR use string directly
        if isinstance(chunk, dict):
            chunk_text = chunk['text']  # Get text from dictionary
            chunk_metadata = chunk.get('metadata', {})
        else:
            chunk_text = chunk  # Already a string
            chunk_metadata = {}
        
        chunk_lower = chunk_text.lower()
        score = 0
        
        # Check each question word
        for word in question_words:
            if word in chunk_lower:
                # Base score: word length
                score += len(word) * 2
                
                # Bonus: Exact word match
                if f" {word} " in f" {chunk_lower} ":
                    score += 5
                
                # Bonus: Word appears multiple times
                occurrences = chunk_lower.count(word)
                if occurrences > 1:
                    score += (occurrences - 1) * 3
        
        if score > 0:
            scored_chunks.append({
                'score': score,
                'text': chunk_text,
                'metadata': chunk_metadata,
                'original_chunk': chunk  # Keep reference to original
            })
    
    # 3. Sort and return top results
    scored_chunks.sort(reverse=True, key=lambda x: x['score'])
    
    return scored_chunks[:top_k]

def load_and_chunk_documents(docs_path: str = "documents"):
    """Improved document loading with metadata"""
    chunker = ImprovedChunker(max_tokens=500, overlap_tokens=50)
    all_chunks = []
    
    for filename in os.listdir(docs_path):
        if not (filename.endswith(".txt") or filename.endswith(".pdf")):
            continue
            
        file_path = os.path.join(docs_path, filename)
        text = ""
        
        # Extract metadata
        base_metadata = {
            'filename': filename,
            'file_type': 'pdf' if filename.endswith('.pdf') else 'txt'
        }
        
        if filename.endswith(".txt"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
                base_metadata['encoding'] = 'utf-8'
            except UnicodeDecodeError:
                # Try other encodings
                for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                    try:
                        with open(file_path, "r", encoding=encoding) as f:
                            text = f.read()
                        base_metadata['encoding'] = encoding
                        break
                    except:
                        continue
        
        elif filename.endswith(".pdf"):
            reader = PdfReader(file_path)
            base_metadata.update({
                'num_pages': len(reader.pages),
                'author': reader.metadata.get('/Author', ''),
                'title': reader.metadata.get('/Title', '')
            })
            
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    # Chunk each page separately with page metadata
                    page_metadata = {
                        **base_metadata,
                        'page_number': page_num + 1
                    }
                    
                    chunks = chunker.smart_chunk(page_text, page_metadata)
                    all_chunks.extend(chunks)
            
            continue  # Already processed pages
        
        # For TXT files, chunk entire content
        if text:
            chunks = chunker.smart_chunk(text, base_metadata)
            all_chunks.extend(chunks)
    
    return all_chunks

def load_all_documents():
    content = ""

    for filename in os.listdir(DOCS_PATH):
        file_path = os.path.join(DOCS_PATH, filename)

        # 📄 Handle TXT files
        if filename.endswith(".txt"):
            with open(file_path, "r", encoding="utf-8") as f:
                content += f.read() + "\n"

        # 📕 Handle PDF files
        elif filename.endswith(".pdf"):
            reader = PdfReader(file_path)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    content += text + "\n"

    return content
