document.addEventListener('DOMContentLoaded', function() {
    console.log("✅ Page loaded. Initializing script...");

    // --- Global variables to store data ---
    let latestHeaderData = null;
    let latestLineItems = [];
    let rawTextContext = "";
    let apiKey = ""; // This should be retrieved from an input

    // --- Get all the HTML elements ---
    const fileUpload = document.getElementById('file-upload');
    const processBtn = document.getElementById('process-btn');
    const sendBtn = document.getElementById('send-btn');
    const downloadBtn = document.getElementById('download-btn');
    const statusDiv = document.getElementById('status');
    const filePreview = document.getElementById('file-preview');
    const tablesContainer = document.getElementById('tables-container');
    const chatInput = document.getElementById('chat-input');
    const barCanvas = document.getElementById('barChart');

    // --- Attach Event Listeners ---

    if (fileUpload) {
        fileUpload.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                filePreview.innerText = `Selected file: ${file.name}`;
            }
        });
    }

    if (processBtn) {
        processBtn.addEventListener('click', handleProcessDocument);
    }

    if (sendBtn) {
        sendBtn.addEventListener('click', handleSendMessage);
    }

    if (downloadBtn) {
        // This is the listener for your button.
        downloadBtn.addEventListener('click', handleDownload);
        console.log("✅ Download button listener attached.");
    } else {
        console.error("❌ Download button with id 'download-btn' was not found!");
    }

    // --- Handler Functions ---

    async function handleProcessDocument() {
        if (fileUpload.files.length === 0) {
            statusDiv.innerText = "Please select a file first.";
            return;
        }
        statusDiv.innerText = "Processing document...";
        const formData = new FormData();
        formData.append('file', fileUpload.files[0]);

        try {
            const response = await fetch('https://ai-document-analyzer-ocr.onrender.com/', { method: 'POST', body: formData });
            if (!response.ok) throw new Error(`Server error: ${response.statusText}`);
            const data = await response.json();

            rawTextContext = data.raw_text;
            latestHeaderData = data.header_data;
            latestLineItems = data.line_items;

            displayTables(latestHeaderData, latestLineItems);
            renderCharts(latestLineItems);
            statusDiv.innerText = "Processing Complete!";
        } catch (error) {
            statusDiv.innerText = `Error: ${error.message}`;
        }
    }

    async function handleSendMessage() {
        // Your existing chat logic
        // This should be updated to get the API key from an input in your HTML
        apiKey = "Error: Please enter your OpenRouter API key first.";
        if (chatInput.value.trim() === "") return;
        const userQuestion = chatInput.value;
        addChatBubble(userQuestion, 'user');
        chatInput.value = "";

        try {
            const response = await fetch('https://ai-document-analyzer-ocr.onrender.com/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: userQuestion, context: rawTextContext, api_key: apiKey })
            });
            if (!response.ok) throw new Error(`Server error: ${response.statusText}`);
            const data = await response.json();
            addChatBubble(data.response, 'bot');
        } catch (error) {
            addChatBubble(`Error: ${error.message}`, 'bot');
        }
    }

    async function handleDownload() {
        console.log("Download button clicked!"); // Check if this message appears
        if (!latestHeaderData) {
            statusDiv.innerText = "Please process a document first.";
            return;
        }
        statusDiv.innerText = "Generating Excel file...";
        try {
            const response = await fetch('https://ai-document-analyzer-ocr.onrender.com/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ header_data: latestHeaderData, line_items: latestLineItems })
            });
            if (!response.ok) throw new Error(`Server error: ${response.statusText}`);

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            const disposition = response.headers.get('Content-Disposition');
            const filenameMatch = disposition ? disposition.match(/filename="(.+?)"/) : null;
            a.download = filenameMatch ? filenameMatch[1] : 'invoice_report.xlsx';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
            statusDiv.innerText = "Excel file downloaded successfully.";
        } catch (error) {
            statusDiv.innerText = `Error generating download: ${error.message}`;
        }
    }

    // --- UI Update Functions ---
    function displayTables(headerData, lineItems) {
        tablesContainer.innerHTML = `
            <h3>Summary</h3>
            <p><strong>Invoice Number:</strong> ${headerData['Invoice Number']}</p>
            <p><strong>Date:</strong> ${headerData['Date']}</p>
            <p><strong>Total Amount:</strong> ${headerData['Total Amount']}</p>
            <h3>Line Items</h3>
            <table>
                <thead><tr><th>Description</th><th>Amount</th></tr></thead>
                <tbody>${lineItems.map(item => `<tr><td>${item.description}</td><td>${item.amount}</td></tr>`).join('')}</tbody>
            </table>`;
    }

    function addChatBubble(text, sender) {
        const chatContainer = document.getElementById('chat-container');
        const bubble = document.createElement('div');
        bubble.classList.add('chat-bubble', sender === 'user' ? 'user-bubble' : 'bot-bubble');
        bubble.innerText = text;
        chatContainer.appendChild(bubble);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    function renderCharts(lineItems) {
        if (!barCanvas) return; // Don't do anything if the chart canvas isn't on the page
        if (window.myBarChart) { window.myBarChart.destroy(); } // Clear old chart
        if (!lineItems || lineItems.length === 0) return;

        const ctx = barCanvas.getContext('2d');
        window.myBarChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: lineItems.map(item => item.description),
                datasets: [{
                    label: 'Amount',
                    data: lineItems.map(item => item.amount),
                    backgroundColor: '#4a90e2'
                }]
            }
        });
    }
});