import io
import json
import logging
import asyncio
from typing import Optional, Tuple, List, Dict, Any
from pypdf import PdfReader
from pypdf.errors import PdfReadError, FileNotDecryptedError

import config
from bot.database.models import StudentModel, StudyMaterialModel
from bot.database.repositories import materials as mat_repo
from bot.services import gemini as gemini_service
from bot.services.storage import default_storage, sanitize_filename

# Chunking thresholds
MAX_DIRECT_TEXT_CHARS = 24000
CHUNK_SIZE_CHARS = 4000
CHUNK_OVERLAP_CHARS = 400

def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> Tuple[str, int, str, Optional[str]]:
    """
    Extracts text, page count, and extraction status from raw PDF bytes.
    Returns (extracted_text, page_count, status, error_message).
    """
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        
        if reader.is_encrypted:
            try:
                # Try empty password
                reader.decrypt("")
            except Exception:
                return "", 0, "ENCRYPTED", "Password-protected PDF files cannot be processed."
                
        page_count = len(reader.pages)
        if page_count == 0:
            return "", 0, "EMPTY", "The PDF document contains no pages."
            
        text_parts = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            if page_text.strip():
                text_parts.append(f"--- Page {i+1} ---\n{page_text.strip()}")
                
        full_text = "\n\n".join(text_parts).strip()
        if not full_text:
            return "", page_count, "SCANNED", "No readable text found (document might be scanned images)."
            
        return full_text, page_count, "SUCCESS", None
    except FileNotDecryptedError:
        return "", 0, "ENCRYPTED", "Document is encrypted and password-protected."
    except PdfReadError as pe:
        logging.error(f"Corrupt PDF encountered: {pe}")
        return "", 0, "CORRUPT", f"Corrupt PDF file: {str(pe)}"
    except Exception as e:
        logging.error(f"Error extracting text with pypdf: {e}", exc_info=True)
        return "", 0, "FAILED", f"Extraction error: {str(e)}"

def chunk_pdf_text(text: str, chunk_size: int = CHUNK_SIZE_CHARS, overlap: int = CHUNK_OVERLAP_CHARS) -> List[str]:
    """Splits large document text into overlapping segments."""
    if len(text) <= chunk_size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += (chunk_size - overlap)
    return chunks

def retrieve_relevant_chunks(chunks: List[str], query: str, top_k: int = 3) -> str:
    """Keyword-based ranking retrieval for query context against chunks."""
    if len(chunks) <= 1:
        return chunks[0] if chunks else ""
    query_words = set(re_word for re_word in query.lower().split() if len(re_word) > 2)
    if not query_words:
        return "\n\n...\n\n".join(chunks[:top_k])
        
    scored = []
    for chunk in chunks:
        chunk_lower = chunk.lower()
        score = sum(1 for w in query_words if w in chunk_lower)
        scored.append((score, chunk))
        
    scored.sort(key=lambda x: x[0], reverse=True)
    top_chunks = [c for s, c in scored[:top_k]]
    return "\n\n...\n\n".join(top_chunks)

async def process_and_save_pdf(
    telegram_id: int,
    pdf_bytes: bytes,
    original_filename: str,
    file_id: Optional[str] = None,
    student: Optional[StudentModel] = None
) -> StudyMaterialModel:
    """
    Saves PDF file using StorageProvider, extracts text, generates topics & summary, and creates DB record.
    """
    # 1. Validate file size
    size_mb = len(pdf_bytes) / (1024 * 1024)
    if size_mb > config.MAX_FILE_SIZE_MB:
        raise ValueError(f"File exceeds maximum allowed size of {config.MAX_FILE_SIZE_MB}MB.")
        
    # 2. Extract text and validate PDF integrity
    extracted_text, page_count, status, error_msg = await asyncio.to_thread(extract_text_from_pdf_bytes, pdf_bytes)
    
    # 3. Save to storage
    disk_path, safe_name = await default_storage.save_file(telegram_id, original_filename, pdf_bytes)
        
    # 4. Handle text analysis and summaries
    if status == "SUCCESS" and extracted_text and student:
        # Use first 20k chars for summary to avoid huge prompt payloads
        summary_source = extracted_text[:20000]
        title, topics, summary = await gemini_service.extract_pdf_topics_and_summary(
            summary_source, safe_name, student
        )
    elif status == "SCANNED":
        title = safe_name
        topics = ["Scanned Document"]
        summary = "Scanned PDF document uploaded. (No direct digital text extractable)."
        extracted_text = f"Document: {safe_name} (Scanned Image PDF)"
    else:
        title = safe_name
        topics = ["Uploaded PDF"]
        summary = f"PDF uploaded (Status: {status})"
        if not extracted_text:
            extracted_text = f"Document: {safe_name} ({error_msg or status})"
            
    topics_json = json.dumps(topics)
    
    # 5. Persist to database
    material = await asyncio.to_thread(
        mat_repo.save_study_material,
        telegram_id=telegram_id,
        filename=safe_name,
        file_path=disk_path,
        file_id=file_id,
        file_size=len(pdf_bytes),
        mime_type="application/pdf",
        title=title,
        page_count=page_count,
        extracted_text=extracted_text,
        summary=summary,
        topics_json=topics_json,
        extraction_status=status,
        extraction_error=error_msg
    )
    return material

async def get_active_material(telegram_id: int) -> Optional[StudyMaterialModel]:
    """Retrieves student's active study material."""
    return await asyncio.to_thread(mat_repo.get_active_study_material, telegram_id)

async def get_student_materials(telegram_id: int, limit: int = 20) -> List[StudyMaterialModel]:
    """Retrieves all non-deleted study materials uploaded by student."""
    return await asyncio.to_thread(mat_repo.get_all_student_materials, telegram_id, limit)

async def activate_student_material(telegram_id: int, material_id: int) -> bool:
    """Sets a specific material as active for the student."""
    return await asyncio.to_thread(mat_repo.set_active_material, telegram_id, material_id)

async def delete_student_material(telegram_id: int, material_id: int) -> bool:
    """Deletes material from database and deletes physical file from storage."""
    material = await asyncio.to_thread(mat_repo.get_study_material_by_id, material_id)
    if not material or material.telegram_id != telegram_id:
        return False
        
    # Delete from DB
    db_deleted = await asyncio.to_thread(mat_repo.delete_study_material, telegram_id, material_id)
    # Delete from physical storage
    if material.file_path:
        await default_storage.delete_file(material.file_path)
    return db_deleted

async def ask_pdf_question(
    telegram_id: int,
    question: str,
    student: StudentModel,
    material: Optional[StudyMaterialModel] = None
) -> str:
    """Grounded question answering against the active or specified PDF document with chunking support."""
    target_mat = material or await get_active_material(telegram_id)
    if not target_mat or not target_mat.extracted_text:
        return "No active PDF document found. Please upload a PDF using /pdf first."
        
    full_text = target_mat.extracted_text
    
    # If text is very large, retrieve relevant chunks
    if len(full_text) > MAX_DIRECT_TEXT_CHARS:
        chunks = chunk_pdf_text(full_text)
        relevant_text = retrieve_relevant_chunks(chunks, question, top_k=4)
    else:
        relevant_text = full_text
        
    return await gemini_service.ask_gemini_with_pdf_context(
        question=question,
        pdf_text=relevant_text,
        pdf_title=target_mat.title or target_mat.filename,
        student=student
    )
