# AI Proofreader

A web-based proofreader that utilizes LLM for intelligent text correction.

## Features

- **Sentence-level Analysis**: Processes text sentence by sentence for precise corrections
- **Visual Diff Interface**: Shows word-level changes with clear highlighting
- **Accept/Reject Controls**: Individual control over each suggested correction
- **Modern UI**: Clean, responsive interface with smooth interactions
- **LLM Integration Ready**: Backend designed for easy integration with various LLM providers

## Architecture

### Backend (Python/FastAPI)
- **Framework**: FastAPI for high-performance API
- **Diff Generation**: Built-in difflib for word-level comparisons
- **LLM Ready**: Modular design for easy LLM provider integration

### Frontend (HTML/CSS/JavaScript)
- **Responsive Design**: Works on desktop and mobile devices
- **Real-time Updates**: Dynamic UI updates without page reloads
- **Keyboard Shortcuts**: Ctrl/Cmd+Enter to proofread
- **Copy Functionality**: Easy copying of final corrected text

## Installation

1. **Clone and navigate to the project:**
   ```bash
   cd /path/to/ai-proofread
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up configuration:**
   ```bash
   # Copy the template configuration file
   cp config_template.py config.py
   
   # Edit config.py and add your OpenRouter API key
   # Get your API key from: https://openrouter.ai/keys
   ```

4. **Run the application:**
   ```bash
   python app.py
   ```

5. **Open your browser:**
   Navigate to `http://localhost:8000`

## Usage

1. **Enter Text**: Paste or type your text in the input area
2. **Proofread**: Click "Proofread Text" or use Ctrl/Cmd+Enter
3. **Review Changes**: Each sentence with corrections will be displayed with:
   - Original text with deletions highlighted in red
   - Corrected text with additions highlighted in green
4. **Accept/Reject**: Use individual buttons or bulk actions
5. **Copy Result**: Copy the final corrected text to clipboard


## API Endpoints

### POST /api/proofread
Processes text and returns sentence-level corrections.

**Request:**
```json
{
  "text": "Your text to proofread",
  "llm_provider": "mock"
}
```

**Response:**
```json
{
  "sentence_diffs": [
    {
      "original": "Original sentence",
      "corrected": "Corrected sentence",
      "changes": [
        {
          "type": "delete|insert|equal",
          "text": "word",
          "position": 0
        }
      ],
      "sentence_index": 0
    }
  ]
}
```

## Customization

### Styling
Modify `static/style.css` to customize the appearance. The design uses CSS custom properties for easy theming.

### Functionality
Extend `static/script.js` to add new features like:
- Batch processing of multiple documents
- Export to different formats
- Integration with document editors
- Custom correction rules

## Development

### Project Structure
```
ai-proofread/
├── app.py              # FastAPI backend
├── config.py           # Configuration file (not in version control)
├── config_template.py  # Template for configuration setup
├── requirements.txt    # Python dependencies
├── static/
│   ├── index.html     # Main HTML interface
│   ├── style.css      # Styling and responsive design
│   └── script.js      # Frontend JavaScript logic
└── README.md          # This file
```

### Adding New Features
1. Backend changes go in `app.py`
2. Frontend changes go in `static/` files
3. New dependencies should be added to `requirements.txt`

## License

MIT License - feel free to use and modify for your needs.
