from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import re
import difflib
from typing import List

from openai import OpenAI
import time
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, DEFAULT_MODEL, TEMPERATURE, MAX_TOKENS



app = FastAPI(title="AI Proofreader", description="Web-based proofreader with LLM integration")

# Initialize OpenRouter client
client = OpenAI(
    base_url=OPENROUTER_BASE_URL,
    api_key=OPENROUTER_API_KEY,
)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

class ProofreadRequest(BaseModel):
    text: str
    llm_provider: str = "mock"  # Will be extended later for actual LLM integration

class ProofreadResponse(BaseModel):
    final_text: str
    total_changes: int

def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences using period as delimiter."""
    sentences = text.split('.')
    return [s.strip() for s in sentences if s.strip()]

def segment_text_by_latex_environments(text: str) -> List[dict]:
    """Split the document into segments, separating out figure/table environments.

    Returns a list of dicts: {"type": "latex"|"text", "content": str}
    """
    env_pattern = re.compile(r"\\begin\{(figure\*?|table\*?)\}[\s\S]*?\\end\{\1\}", re.MULTILINE)
    segments = []
    last_idx = 0
    for match in env_pattern.finditer(text):
        start, end = match.start(), match.end()
        if start > last_idx:
            segments.append({"type": "text", "content": text[last_idx:start]})
        segments.append({"type": "latex", "content": text[start:end]})
        last_idx = end
    if last_idx < len(text):
        segments.append({"type": "text", "content": text[last_idx:]})
    return segments

def split_paragraphs_with_separators(text_block: str) -> List[str]:
    """Split a text block into paragraphs, preserving the exact separators.

    We treat paragraphs as blocks separated by at least one blank line.
    The returned list alternates between content and separator strings because we use a capturing group.
    """
    parts = re.split(r"(\n\s*\n+)", text_block)
    return parts

def llm_correct_paragraph(previous_paragraph: str, current_paragraph: str) -> str:
    """Ask the LLM to proofread only the second paragraph (current), using the previous paragraph as context."""
    try:
        prev_text = previous_paragraph.strip()
        curr_text = current_paragraph.strip()

        prompt = f"""You are a professional proofreader and editor for LaTeX scientific writing.

You will be given two paragraphs:
- P1 (previous paragraph): may be empty
- P2 (current paragraph): this is the ONLY paragraph you must correct

Instructions:
1. Correct grammar and improve flow in P2 ONLY. Do not change P1.
2. Preserve meaning and tone. Maintain sentence count when possible.
3. Do not modify any LaTeX commands or math (e.g., \cite, \ref, \begin, \end, $...$, \textbf{{...}}).
4. Return ONLY the corrected P2 content, with no extra commentary.
5. If no corrections are needed, return P2 exactly as provided.

P1 (previous paragraph):
"""
        if prev_text:
            prompt += prev_text + "\n\n"
        else:
            prompt += "(empty)\n\n"

        prompt += "P2 (current paragraph to correct):\n" + curr_text + "\n\nCorrected P2:"

        completion = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        time.sleep(1)
        corrected = completion.choices[0].message.content.strip()
        if corrected.startswith('"') and corrected.endswith('"'):
            corrected = corrected[1:-1]
        return corrected
    except Exception as e:
        print(f"Error calling LLM: {str(e)}")
        return current_paragraph

def count_word_level_changes(original: str, corrected: str) -> int:
    """Count total word-level changes between two texts.

    We count inserts + deletes, and for replacements count max(len_block_original, len_block_corrected).
    """
    original_words = original.split()
    corrected_words = corrected.split()
    differ = difflib.SequenceMatcher(None, original_words, corrected_words)
    changes = 0
    for tag, i1, i2, j1, j2 in differ.get_opcodes():
        if tag == 'replace':
            changes += max(i2 - i1, j2 - j1)
        elif tag == 'delete':
            changes += (i2 - i1)
        elif tag == 'insert':
            changes += (j2 - j1)
    return changes

def build_final_text_with_paragraph_corrections(text: str) -> str:
    """Process the text: skip LaTeX figure/table envs and correct only paragraphs (>2 sentences).

    For each qualifying paragraph, pass (previous_paragraph, current_paragraph) to the LLM and replace
    the current paragraph with the corrected version. Non-qualifying blocks and LaTeX envs remain unchanged.
    """
    segments = segment_text_by_latex_environments(text)
    rebuilt_segments: List[str] = []
    last_text_paragraph_for_context = ""

    for seg in segments:
        if seg["type"] == "latex":
            rebuilt_segments.append(seg["content"])  # leave unchanged
            continue

        # Process text content, preserving paragraph separators
        parts = split_paragraphs_with_separators(seg["content"])  # [para, sep, para, sep, ...]
        corrected_parts: List[str] = []

        for idx, part in enumerate(parts):
            # Separator blocks (captured) are kept verbatim
            if idx % 2 == 1:
                corrected_parts.append(part)
                continue

            # Content block
            content_block = part
            if not content_block.strip():
                corrected_parts.append(content_block)
                continue

            # Count sentences to decide if it's a paragraph per our rule (> 2 sentences)
            # Replace line breaks with spaces for more reliable sentence tokenization
            sentence_count = len(split_into_sentences(content_block.replace("\n", " ")))
            if sentence_count > 2:
                corrected_para = llm_correct_paragraph(last_text_paragraph_for_context, content_block)
                corrected_parts.append(corrected_para)
                last_text_paragraph_for_context = corrected_para
            else:
                corrected_parts.append(content_block)
                # only update context when it looks like a true paragraph
                # so we skip updating context here

        rebuilt_segments.append("".join(corrected_parts))

    return "".join(rebuilt_segments)

@app.post("/api/proofread", response_model=ProofreadResponse)
async def proofread_text(request: ProofreadRequest):
    """Process text and return the fully corrected text plus a total change count.

    Requirements:
    - Do not send LaTeX figure/table environments to the LLM; leave them unchanged
    - Define a paragraph as a block with > 2 sentences
    - For each such paragraph, pass (previous, current) to the LLM and correct ONLY the current
    """
    try:
        print(f"Received text: {request.text[:100]}...")
        final_text = build_final_text_with_paragraph_corrections(request.text)
        total_changes = count_word_level_changes(request.text, final_text)
        return ProofreadResponse(final_text=final_text, total_changes=total_changes)
    except Exception as e:
        print(f"Error in proofread_text: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def read_index():
    """Serve the main HTML page."""
    return FileResponse('static/index.html')

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)