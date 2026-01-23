import streamlit as st
import cv2
import pytesseract
import re
import pandas as pd
import numpy as np
import io
from openai import OpenAI
import os
import fitz

# --- Configuration ---
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# --- CORE PROCESSING & AI FUNCTIONS ---

def get_openai_response(question, context, api_key):
    try:
        client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
        messages = [
            {
                "role": "system",
                "content": """You are an expert financial assistant who reads and understands invoice documents.
                            Based *only* on the text provided below, answer the user's question accurately.

                         

                           
            },
            {
                "role": "user",
                "content": f"""Here is the document text:
                               ---
                               {context}
                               ---
                               My question is: {question}"""
            }
        ]
        response = client.chat.completions.create(
            model="anthropic/claude-3-haiku",
            messages=messages,
            temperature=0,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: Could not get a response from the OpenRouter model. Details: {e}"


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


# --- STREAMLIT APP ---

st.set_page_config(page_title="Document Analyzer AI", page_icon="🧾")
st.title("🧾 Document Analyzer AI")

with st.sidebar:
    st.header("Configuration")
    openai_api_key = st.text_input("Enter OpenRouter API Key:", type="password",
                                   help="Get your key from https://openrouter.ai/keys")

if 'processing_done' not in st.session_state:
    st.session_state.processing_done = False
if 'raw_text' not in st.session_state:
    st.session_state.raw_text = ""
if "messages" not in st.session_state:
    st.session_state.messages = []


# (Helper function and file uploader are unchanged)
def load_file_as_image(uploaded_file):
    raw_bytes = uploaded_file.getvalue()
    if uploaded_file.type == "application/pdf":
        try:
            pdf_document = fitz.open(stream=raw_bytes, filetype="pdf")
            first_page = pdf_document.load_page(0)
            pixmap = first_page.get_pixmap()
            image = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(pixmap.height, pixmap.width, pixmap.n)
            if image.shape[2] == 3:
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            return image
        except Exception as e:
            st.error(f"Error processing PDF: {e}")
            return None
    else:
        file_bytes_np = np.asarray(bytearray(raw_bytes), dtype=np.uint8)
        return cv2.imdecode(file_bytes_np, 1)


uploaded_file = st.file_uploader("Upload a document (Image or PDF)", type=["png", "jpg", "jpeg", "pdf"])

if uploaded_file is not None:
    if st.session_state.get('uploaded_filename') != uploaded_file.name:
        st.session_state.processing_done = False
        st.session_state.messages = []
        st.session_state.uploaded_filename = uploaded_file.name

    image = load_file_as_image(uploaded_file)

    if image is not None:
        display_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        st.image(display_image, caption="Document Preview (First Page)", use_column_width=True)

        if st.button("Process Document"):
            with st.spinner("Analyzing your document..."):
                all_text = []
                # Re-read file bytes as getvalue() can only be read once
                raw_bytes = uploaded_file.getvalue()
                if uploaded_file.type == "application/pdf":
                    pdf_document = fitz.open(stream=raw_bytes, filetype="pdf")
                    for page_num in range(len(pdf_document)):
                        page = pdf_document.load_page(page_num)
                        pix = page.get_pixmap(dpi=200)
                        page_image = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
                        if page_image.shape[2] == 3:
                            page_image = cv2.cvtColor(page_image, cv2.COLOR_RGB2BGR)
                        gray = cv2.cvtColor(page_image, cv2.COLOR_BGR2GRAY)
                        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
                        all_text.append(pytesseract.image_to_string(thresh))
                    extracted_text = "\n".join(all_text)
                else:
                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
                    extracted_text = pytesseract.image_to_string(thresh)

                st.session_state.raw_text = extracted_text
                st.session_state.processing_done = True
                st.session_state.messages = []
                st.success("Document processed successfully! You can now ask questions below.")

    if st.session_state.processing_done:
        st.info("The tables below are editable! Double-click any cell to make corrections.")
        line_items = extract_line_items(st.session_state.raw_text)
        calculated_total = sum(item['amount'] for item in line_items)
        invoice_data = parse_universal_invoice(st.session_state.raw_text, calculated_total)

        df_header = pd.DataFrame([invoice_data])
        df_items = pd.DataFrame(line_items)
        edited_df_header = st.data_editor(df_header, use_container_width=True, key="header_editor")
        if not df_items.empty:
            edited_df_items = st.data_editor(df_items, use_container_width=True, key="items_editor")

        # --- NEW FEATURE: DATA VISUALIZATION ---
        st.subheader("📊 Cost Breakdown by Item")
        if not edited_df_items.empty:
            # Prepare data for charting by setting the description as the index
            chart_data = edited_df_items.set_index('description')['amount']
            st.bar_chart(chart_data)
            st.write("This chart shows the amount for each extracted line item.")
        else:
            st.warning("No line items were extracted to create a chart.")
        # ------------------------------------

        st.subheader("💾 Download Corrected Data")

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            edited_df_header.to_excel(writer, sheet_name='Summary', index=False)
            if not edited_df_items.empty:
                edited_df_items.to_excel(writer, sheet_name='Line Items', index=False)

        invoice_num = edited_df_header.iloc[0]['Invoice Number']
        st.download_button(
            label="📥 Download Excel Report",
            data=output.getvalue(),
            file_name=f"invoice_{invoice_num}_corrected.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.subheader("💬 Chat with your Document")

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("What is the Total Due?"):
            if not openai_api_key:
                st.warning("Please enter your OpenRouter API Key in the sidebar first.")
            else:
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        response = get_openai_response(prompt, st.session_state.raw_text, openai_api_key)
                        st.markdown(response)

                st.session_state.messages.append({"role": "assistant", "content": response})

