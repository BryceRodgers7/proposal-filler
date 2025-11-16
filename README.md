# AI-Powered Resume Form Filler

A Streamlit web application that uses AI to automatically extract structured information from resume files (PDF, DOCX, or TXT) and populate an editable form.

## Features

- 📄 **Multi-format Support**: Upload resumes in PDF, DOCX, or TXT format
- 🤖 **AI-Powered Extraction**: Uses OpenAI's GPT models to intelligently extract key information
- ✏️ **Editable Form**: Review and edit extracted data before exporting
- 📥 **JSON Export**: Download structured resume data as JSON
- 🔍 **Debug Mode**: View raw extracted text for troubleshooting

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd resume-filler
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Setup

### OpenAI API Key

You need an OpenAI API key to use the AI extraction feature. You can configure it in one of two ways:

**Option 1: Streamlit Secrets (Recommended for local development)**

Create a `.streamlit/secrets.toml` file in the project root:

```toml
[secrets]
OPENAI_API_KEY = "sk-your-api-key-here"
```

**Option 2: Environment Variable**

Set the `OPENAI_API_KEY` environment variable:

```bash
# Windows (PowerShell)
$env:OPENAI_API_KEY="sk-your-api-key-here"

# Linux/Mac
export OPENAI_API_KEY="sk-your-api-key-here"
```

## Usage

1. Start the Streamlit app:
```bash
streamlit run main.py
```

2. Open your browser to the URL shown in the terminal (usually `http://localhost:8501`)

3. Upload a resume file (PDF, DOCX, or TXT)

4. Click "Extract with AI" to automatically populate the form fields

5. Review and edit the extracted information as needed

6. Download the structured data as JSON using the "Download as JSON" button

## Extracted Fields

The app extracts the following information:
- Full name
- Email
- Phone number
- Professional summary
- Most recent job title
- Company name
- Employment start date
- Employment end date
- Job description

## Requirements

- Python 3.7+
- OpenAI API key
- See `requirements.txt` for Python package dependencies

## License

[Add your license here]

