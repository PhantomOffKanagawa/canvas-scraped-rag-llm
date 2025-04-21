# Canvas Scraper

A comprehensive toolkit for extracting, processing, and interacting with Canvas LMS content, with a focus on quiz management and content retrieval.

>[!IMPORTANT]
> Obligatory Disclaimer: DO NOT USE FOR ACADEMIC DISHONESTY \
> It is a good study tool for collecting canvas materials and using a vector DB to quickly grab relevant materials. Querying against it is generally better than a generic chat model. \
> The Chrome Extension was built during a bout of boredom during an open-note, untimed quiz and tested exclusively on completed quizzes \
> It also needs refinement for actual use to avoid issues like answering a question from RAG material. TL;DR DON'T CHEAT, it's honestly not even that good for it 

That said it was a mostly one-night no sleep passion project that I'm proud of learning a basic RAG implementation and API scraper for so here it is.

## Overview

Canvas Scraper is a collection of Python scripts and a Chrome extension designed to:

1. Extract course content from Canvas LMS using the Canvas API
2. Process and transform course materials including pages, modules, and quizzes
3. Provide quiz assistance through a browser extension
4. Create searchable vector embeddings from course content
5. Enable AI-assisted quiz taking through OpenAI integration

## Components

### Python Scripts

- **01_scraper.py**: Main scraper that extracts course modules, pages, and quiz URLs using Canvas API
- **01b_pdf_scraper.py**: Extracts and downloads PDF files linked in Canvas content
- **01c_quiz_converter.py**: Converts quiz data to standardized formats
- **02_tokenizer.py**: Breaks down information stores to tokens
- **03_vectorize.py**: Creates vector embeddings from course content tokens for semantic search
- **04_chat.py**: Basic hard-coded script for querying course content using RAG (Retrieval-Augmented Generation)
- **05_api.py**: Flask API server for the quiz helper extension to query course content

### Chrome Extension

The `canvas-quiz-extension` directory contains a Chrome extension with features:

- Extract quiz questions from Canvas quiz pages
- Process questions using either:
  - OpenAI API (gpt-4o-mini)
  - Local RAG-based API (connecting to 05_api.py)
  - Copy mode for manual pasting into other tools
- Display formatted answers with relevant context from course materials

## Setup

### Prerequisites

- Python 3.7+
- Chromium based browser (for extension)
- Canvas LMS account with API access
- OpenAI API key (optional)

### Environment Setup

1. Clone the repository
   ```
   git clone <repository-url>
   cd canvas-scraper
   ```

2. Create a `.env` file in the project root with the following variables:
   ```
   CANVAS_DOMAIN=your-institution.instructure.com
   CANVAS_API_KEY=your_canvas_api_key
   OPENAI_API_KEY=your_openai_api_key
   ```

3. Install Python dependencies
   ```
   pip install requests beautifulsoup4 python-dotenv openai fitz chromadb flask flask-cors
   ```

### Extension Installation (For Chrome)

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked" and select the `canvas-quiz-extension` directory
4. The Canvas Quiz Helper extension should now be available

> **Note** Other browsers like Edge also support this extension, but installation steps may vary.

## Usage

> **Warning** Steps below are likely not as simple as they should be. The code is a work in progress and may require adjustments.

### Data Extraction

1. Run the main scraper to extract course content:
   ```
   python3 01_scraper.py
   ```

2. Extract PDF files from course content:
   ```
   python3 01b_pdf_scraper.py
   ```

3. Extract Quiz Data manually:
    - Use the `bookmarklet.js` file on a bookmarklet creation site to create a bookmarklet
    - Navigate to the quiz pages in Canvas as listed in `quiz_urls.txt`
    - Click the bookmarklet to extract quiz data
    - Copy the output to a file named `quiz_[QUIZ_NAME].json` in the a directory under the script named `quiz_json`

4. Convert quiz data to standardized format:
   ```
   python3 01c_quiz_converter.py
   ```

### Creating Vector Database

1. Process extracted content into vector embeddings:
   ```
   python3 03_vectorize.py
   ```

### Using the API Server

1. Start the local API server for the extension:
   ```
   python3 05_api.py
   ```

### Using the Quiz Helper Extension

1. Navigate to a Canvas quiz page
2. Click the Canvas Quiz Helper extension icon
3. Select your preferred mode (OpenAI API, Local API, or Copy)
4. Use "Extract Current Question" or "Extract All Questions" to process quiz content
5. View AI-generated answers with relevant context from course materials

## Extension Settings

- **OpenAI API Key**: Required for OpenAI API mode
- **Mode Selection**:
  - **OpenAI API**: Uses OpenAI's models for question answering
  - **Local API**: Uses the local RAG-based API (requires 05_api.py running)
  - **Copy**: Copies formatted questions to clipboard for manual processing

## Files and Data

The scraper generates several output files:

- `[COURSE_NAME]_modules.json`: Course module structure
- `[COURSE_NAME]_items.json`: Course page content
- `[COURSE_NAME]_bodies.txt`: Extracted text content
- `[COURSE_NAME]_sanitized_items.json`: Clean text content
- `quiz_[QUIZ_NAME].json`: Extracted quiz questions and answers
- `pdfs/`: Directory containing downloaded PDF files

## Notes

- This tool is designed for educational purposes and personal use
- Respect your institution's terms of service when using the Canvas API
- Some features require an OpenAI API key, which may incur costs
