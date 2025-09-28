import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ContentChunker:
    def __init__(self, max_tokens_per_chunk: int = 512, overlap_tokens: int = 50):
        self.max_tokens_per_chunk = max_tokens_per_chunk
        self.overlap_tokens = overlap_tokens

    def estimate_tokens(self, text: str) -> int:
        return len(text.split())

    def split_by_sentences(self, text: str) -> List[str]:
        sentence_endings = r'[.!?]+\s+'
        sentences = re.split(sentence_endings, text)
        return [s.strip() for s in sentences if s.strip()]

    def chunk_content(self, content: str, title: str = "", is_comment: bool = False) -> List[str]:
        if is_comment and self.estimate_tokens(content) <= self.max_tokens_per_chunk:
            return [content]

        estimated_tokens = self.estimate_tokens(content)

        if estimated_tokens <= self.max_tokens_per_chunk:
            return [content]

        sentences = self.split_by_sentences(content)
        if len(sentences) <= 1:
            words = content.split()
            chunk_size = self.max_tokens_per_chunk - self.estimate_tokens(title) - 5
            chunks = []

            for i in range(0, len(words), chunk_size - self.overlap_tokens):
                chunk_words = words[i:i + chunk_size]
                chunk = ' '.join(chunk_words)
                chunks.append(chunk)

            return chunks

        chunks = []
        current_chunk = []
        current_tokens = 0

        title_tokens = self.estimate_tokens(title) + 5 if title else 0
        available_tokens = self.max_tokens_per_chunk - title_tokens

        for sentence in sentences:
            sentence_tokens = self.estimate_tokens(sentence)

            if current_tokens + sentence_tokens <= available_tokens:
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
            else:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))

                if sentence_tokens <= available_tokens:
                    current_chunk = [sentence]
                    current_tokens = sentence_tokens
                else:
                    words = sentence.split()
                    chunk_size = available_tokens - self.overlap_tokens

                    for i in range(0, len(words), chunk_size):
                        chunk_words = words[i:i + chunk_size]
                        chunks.append(' '.join(chunk_words))

                    current_chunk = []
                    current_tokens = 0

        if current_chunk:
            chunks.append(' '.join(current_chunk))

        if title and chunks:
            chunks = [f"{title}\n\n{chunk}" for chunk in chunks]

        logger.info(f"Content chunked into {len(chunks)} parts (original: {estimated_tokens} tokens)")
        return chunks

    def prepare_chunks_with_metadata(self, content: str, base_metadata: Dict[str, Any], title: str = "", is_comment: bool = False) -> List[Dict[str, Any]]:
        chunks = self.chunk_content(content, title, is_comment)

        prepared_chunks = []
        for i, chunk in enumerate(chunks):
            chunk_metadata = base_metadata.copy()
            chunk_metadata.update({
                "chunk_index": i,
                "total_chunks": len(chunks)
            })

            prepared_chunks.append({
                "content": chunk,
                "metadata": chunk_metadata
            })

        return prepared_chunks

chunker = ContentChunker()