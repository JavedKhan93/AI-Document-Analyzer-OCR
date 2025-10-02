from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import pytesseract
import cv2
import re
import pandas as pd
import numpy as np
import io
from openai import OpenAI
import fitz  # PyMuPDF
from pydantic import BaseModel
from typing import List, Dict, Any

# --- Configuration ---
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- (Helper functions are the same) ---
def extract_line_items(text):
    line_items = []
    pattern = re.compile(r'^\d+\s+(.*?)\s+([\d,]+\.\d{2})$', re.MULTILINE)
    matches = pattern.findall(text)
    for match in matches:
        description = ' '.join(match[0].split())
        amount = match[1]
        line_items.append({'description': description, 'amount': float(amount.replace(',', ''))})
    return line_items


def parse_universal_invoice(text, calculated_total):
    data = {}
    invoice_no_patterns = [r'INVOICE\s+([A-Z0-9]+)']
    date_patterns = [r'Date\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})']

    def search_patterns(patterns, text_to_search):
        for pattern in patterns:
            match = re.search(pattern, text_to_search, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    data['Invoice Number'] = search_patterns(invoice_no_patterns, text) or 'Not Found'
    data['Date'] = search_patterns(date_patterns, text) or 'Not Found'
    data['Total Amount'] = f"{calculated_total:.2f}" if calculated_total > 0 else 'Not Found'
    return data


@app.post("/process-document/")
async def process_document(file: UploadFile = File(...)):
    # (This endpoint is the same)
    try:
        raw_bytes = await file.read()
        extracted_text = ""
        if file.content_type == "application/pdf":
            pdf_document = fitz.open(stream=raw_bytes, filetype="pdf")
            all_text = []
            for page in pdf_document:
                pix = page.get_pixmap(dpi=200)
                page_image = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
                if page_image.shape[2] == 3: page_image = cv2.cvtColor(page_image, cv2.COLOR_RGB2BGR)
                gray = cv2.cvtColor(page_image, cv2.COLOR_BGR2GRAY)
                thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
                all_text.append(pytesseract.image_to_string(thresh))
            extracted_text = "\n".join(all_text)
        else:
            image = cv2.imdecode(np.asarray(bytearray(raw_bytes), dtype=np.uint8), 1)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
            extracted_text = pytesseract.image_to_string(thresh)
        line_items = extract_line_items(extracted_text)
        calculated_total = sum(item['amount'] for item in line_items)
        invoice_data = parse_universal_invoice(extracted_text, calculated_total)
        return {"header_data": invoice_data, "line_items": line_items, "raw_text": extracted_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ChatRequest(BaseModel):
    question: str
    context: str
    api_key: str


@app.post("/chat/")
async def chat_with_document(request: ChatRequest):
    # (This endpoint is the same)
    try:
        client = OpenAI(api_key=request.api_key, base_url="https://openrouter.ai/api/v1")
        messages = [{"role": "system", "content": "You are an expert..."},
                    {"role": "user", "content": f"Context:\n{request.context}\n\nQuestion: {request.question}"}]
        response = client.chat.completions.create(model="anthropic/claude-3-haiku", messages=messages, temperature=0)
        return {"response": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- NEW: API Endpoint for Downloading the Excel File ---
class ExcelRequest(BaseModel):
    header_data: Dict[str, Any]
    line_items: List[Dict[str, Any]]


@app.post("/download-excel/")
async def download_excel(request: ExcelRequest):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_header = pd.DataFrame([request.header_data])
        df_items = pd.DataFrame(request.line_items)
        df_header.to_excel(writer, sheet_name='Summary', index=False)
        if not df_items.empty:
            df_items.to_excel(writer, sheet_name='Line Items', index=False)

    output.seek(0)

    headers = {
        'Content-Disposition': f'attachment; filename="invoice_{request.header_data.get("Invoice Number", "report")}.xlsx"'
    }
    return StreamingResponse(output, headers=headers,
                             media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')