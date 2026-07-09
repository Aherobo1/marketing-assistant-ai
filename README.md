# Marketing Assistant AI

A comprehensive AI-powered tool designed to streamline the process of ideation, copywriting, and marketing campaign creation for Adriana James. This system generates high-quality marketing content that maintains brand consistency while significantly reducing content creation time.


## 🌟 Features

- **AI-Powered Content Generation**: Create marketing content for various channels with customizable parameters
- **Brand Voice Consistency**: Ensure all content adheres to Adriana James' unique brand tone and style
- **Vector Search**: Find similar past content for reference and inspiration
- **Content Improvement**: Refine generated content based on specific feedback
- **Brand Style Management**: Configure and update brand guidelines through a user-friendly interface
- **Training Data Management**: Add successful marketing content to improve the AI over time
- **Content Performance Analysis**: Get insights into the potential effectiveness of your content
- **History Tracking**: Keep track of all generated content and user interactions
- **Pagination Support**: Efficiently browse through large datasets of historical content
- **Error Handling**: Robust error handling and user feedback systems

## 📋 Project Overview

The Marketing Assistant AI combines a powerful backend built with FastAPI and a clean, intuitive frontend interface. It leverages advanced AI models through the Cohere API for text generation, embeddings, and reranking.

### Tech Stack

- **Backend**: Python with FastAPI
- **AI Models**: Cohere's generation and embedding models
- **Vector Database**: FAISS for efficient content similarity search
- **Storage**: 
  - JSON files for historical marketing data
  - SQLite for training data
  - FAISS vector store for content similarity search

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- Node.js and npm (optional, for development tools)
- Cohere API key

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/Aherobo1/marketing-assistant-ai.git
cd marketing-assistant-ai
```

2. **Set up the backend**

```bash
cd backend
pip install -r requirements.txt
```

3. **Configure environment variables**

Create a `.env` file in the project root with the following variables:

```
# API Keys
COHERE_API_KEY=your-api-key-here

# LLM Configuration
LLM_MODEL=llm-model-name # e.g., command
LLM_API_KEY=your-api-key-here # if using a custom model

# Server Configuration
API_HOST=localhost
API_PORT=8000

# Database Configuration
DATABASE_URL=sqlite:///./data/training_data.db

# Brand Configuration
BRAND_NAME=Adriana James
```

4. **Start the backend server**

```bash
cd backend
python main.py
```

The API will be available at http://localhost:8000

## 📁 Project Structure

```
Marketing_Assistant_AI/
│-- backend/
│   │-- main.py                # FastAPI application
│   │-- copywriter.py          # AI content generation
│   │-- vector_store.py        # FAISS vector database
│   │-- embeddings.py          # Cohere embeddings
│   │-- brand_style.py         # Brand style management
│   │-- config.py              # Configuration settings
│   │-- requirements.txt       # Python dependencies
│
│-- data/
│   │-- past_campaigns/        # Stored marketing campaigns
│   │-- user_queries/          # Query history
│   │-- style_guidelines/      # Brand style config
│   │   │-- brand_style.json   # Default style guidelines
│
│-- docs/
│   │-- README.md              # Developer documentation
│   │-- API_Documentation.md   # API reference
│
│-- .env                       # Environment variables
│-- .gitignore                 # Git ignore rules
│-- LICENSE                    # License information
│-- README.md                  # This file
```

## 🔄 API Endpoints

The backend provides several RESTful API endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/generate-copy` | POST | Generate marketing content |
| `/brand-style` | GET | Retrieve brand style guidelines |
| `/brand-style` | PUT | Update brand style guidelines |
| `/training-data` | POST | Add new training data |
| `/training-data` | GET | List available training data |
| `/training-data/{id}` | GET | Get specific training document |
| `/training-data/{id}` | DELETE | Delete training document |
| `/improve-content` | POST | Improve content based on feedback |
| `/analyze-content` | POST | Analyze content performance |

For detailed API documentation, see [API Documentation](docs/API_Documentation.md).

## 💡 How It Works

1. **Content Generation Process**
   - User submits a content request
   - System formats the prompt with brand style guidelines
   - Similar past content is retrieved from the vector database
   - The AI generates content using the formatted prompt and references
   - The system checks alignment with brand guidelines
   - Final content is returned with alignment score and suggestions

2. **Brand Style Management**
   - Brand style guidelines are stored in JSON format
   - The system uses these guidelines to format prompts for the AI
   - Content is checked against taboo words and preferred terminology
   - An alignment score is calculated based on adherence to guidelines

3. **Vector Search**
   - Marketing content is converted to vector embeddings using Cohere
   - FAISS enables efficient similarity search across thousands of documents
   - Similar content is reranked based on relevance to the query

## 🛠️ Development

### Backend Development

The backend is built with FastAPI and follows a modular architecture:

- `main.py`: API endpoints and request handling
- `copywriter.py`: Core AI content generation
- `vector_store.py`: Vector database operations
- `embeddings.py`: Embedding generation and reranking
- `brand_style.py`: Brand style management
- `config.py`: Configuration settings

## 🔍 Future Enhancements

- User authentication and role-based access
- Content performance analytics dashboard
- A/B testing capabilities
- Integration with marketing platforms
- Custom model fine-tuning for even better results
- Mobile application

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👏 Acknowledgements

- [Cohere](https://cohere.ai/) for AI models
- [FastAPI](https://fastapi.tiangolo.com/) for the API framework
- [FAISS](https://github.com/facebookresearch/faiss) for vector search

---

Made with ❤️ for Adriana James
