# RBI Mock Test Generator

A comprehensive system for generating RBI Grade B Phase 1 mock tests using AI.

## 🚀 Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Run Generation Scripts**
   ```bash
   # Generate English questions
   python scripts/generation/generate_english/1_generate_english.py
   
   # Generate Reasoning questions
   python scripts/generation/generate_reasoning/generate_strengthening_weakening_arguments.py
   
   # Generate GA questions
   python scripts/generation/generate_ga/1_generate_ga.py
   ```

## 📁 Project Structure

```
├── config/                 # Configuration files
├── data/                   # Data storage
│   ├── blueprints/        # Test blueprints
│   ├── generated/         # Generated questions
│   └── reference_questions/ # Reference question banks
├── docs/                   # Documentation and resources
│   ├── prompts/           # AI prompts
│   ├── rbi_prev_paper/    # Previous year papers
│   ├── rbi_txt/           # Extracted text from papers
│   └── output_charts/     # Generated charts
├── generated_tests/        # Final test outputs
├── practice-platform/      # Web application (untouched)
├── scripts/                # All Python scripts
│   ├── generation/        # Question generation scripts
│   ├── validation/        # Question validation scripts
│   ├── utilities/         # Utility scripts
│   └── pdf_processing/    # PDF extraction scripts
└── .env                   # Environment variables (not in git)
```

## 🔑 Environment Variables

Create a `.env` file with the following variables:

```env
# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# Google Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here

# Adobe PDF Services API Credentials
ADOBE_CLIENT_ID=your_adobe_client_id
ADOBE_CLIENT_SECRET=your_adobe_client_secret
ADOBE_ORGANIZATION_ID=your_adobe_org_id

# Environment
ENVIRONMENT=development
```

## 📊 Features

- **Question Generation**: Generate questions for English, Reasoning, GA, and Quantitative sections
- **AI Validation**: Validate generated questions using AI
- **PDF Processing**: Extract questions from PDF documents
- **Test Assembly**: Create complete mock tests
- **Web Platform**: Practice platform for taking tests

## 🛠️ Scripts

### Generation Scripts
- `scripts/generation/generate_english/` - English question generation
- `scripts/generation/generate_reasoning/` - Reasoning question generation
- `scripts/generation/generate_ga/` - General Awareness question generation
- `scripts/generation/generate_quant_questions/` - Quantitative question generation

### Validation Scripts
- `scripts/validation/ai_validator.py` - OpenAI-based validation
- `scripts/validation/ai_validator_gemini.py` - Gemini-based validation

### Utility Scripts
- `scripts/utilities/` - Various utility functions
- `scripts/pdf_processing/` - PDF extraction and processing

## 📝 Usage

1. **Generate Questions**: Run the appropriate generation script for each section
2. **Validate Questions**: Use validation scripts to check question quality
3. **Create Tests**: Use test assembly scripts to create complete mock tests
4. **Deploy Platform**: Use the practice-platform for the web interface

## 🔒 Security

- All API keys are stored in environment variables
- `.env` file is gitignored
- No hardcoded credentials in the codebase

## 📄 License

This project is for educational purposes.
