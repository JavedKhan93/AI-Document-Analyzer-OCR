# 🧾 AI Document Analyzer
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)

An intelligent full-stack web application that uses OCR and an AI chatbot to extract, analyze, and answer questions about uploaded invoices and PDF documents.

**Live Demo Link:- https://ai-invoice-analyzer87.netlify.app/

---

## ✨ Key Features

* **Dual File Support:** Seamlessly handles both image files (`.jpg`, `.png`) and **multi-page PDFs**.
* **AI-Powered OCR:** Utilizes Tesseract to accurately convert document images into machine-readable text.
* **Automated Data Extraction:** Employs Regex to automatically find and structure key details like Invoice Number, Date, Line Items, and calculates the Total Amount.
* **Conversational AI Chat:** Features an interactive chatbot powered by an LLM (via OpenRouter) to answer user questions about the document's content in natural language.
* **Interactive UI:** Built with a clean HTML, CSS, and JavaScript frontend that communicates with a powerful Python backend.
* **Export to Excel:** Allows users to download the extracted and verified data into a multi-sheet Excel file for reporting.

## 🛠️ Tech Stack

* **Backend:** Python, FastAPI, Uvicorn
* **Frontend:** HTML5, CSS3, Vanilla JavaScript
* **AI/ML:**
    * Tesseract OCR for text extraction.
    * OpenRouter to access various LLMs for the chat feature.
* **Core Libraries:** OpenCV, PyMuPDF, Pandas, OpenAI

## 🚀 How to Run Locally

To get a local copy up and running, follow these simple steps.

### Prerequisites

You must have Python and the Tesseract OCR engine installed on your system.

### Installation & Setup

1. Clone the repository or download the source code.
2. Install the required Python packages:
    ```sh
    pip install -r requirements.txt
    ```
3. Get a free API key from [OpenRouter.ai](https://openrouter.ai/keys).

### Running the Application

This project has a separate backend and frontend, so you will need to run them in two separate terminals.

1. **Start the Backend Server (Terminal 1):**
    ```sh
    uvicorn backend:app --reload
    ```
2. **Start the Frontend Server (Terminal 2):**
    ```sh
    python -m http.server 9000
    ```
3. Open your browser and navigate to `http://localhost:9000`.

## 👤 Contact

JAVED AHMED KHAN 
LINKEDIN:- https://www.linkedin.com/in/javed-ahmed-khan/
