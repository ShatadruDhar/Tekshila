# Tekshila - AI-Powered Code Documentation

🧠 Transform your code into comprehensive documentation with AI-powered analysis

## Overview

Tekshila is a modern web application that leverages artificial intelligence to automatically generate high-quality documentation for your codebase. Whether you need README files, inline comments, or code quality analysis, Tekshila provides intelligent insights to improve your development workflow.

## Features

### 📝 Documentation Generation
- **Smart README Creation**: Generate comprehensive README files from your codebase
- **Inline Comments**: Add intelligent comments to your code
- **Multi-language Support**: Python, JavaScript, TypeScript, Java, C++, C#, Go, Rust, PHP, Ruby, Swift, and Kotlin
- **Batch Processing**: Upload multiple files or entire projects via ZIP

### 🔗 GitHub Integration
- **Seamless Connection**: Connect to GitHub repositories using personal access tokens
- **Pull Request Automation**: Automatically create pull requests with generated documentation
- **Branch Management**: Choose target branches for your documentation updates
- **Repository Access**: Browse and select from your accessible repositories

### 🔍 Code Quality Analysis
- **AI-Powered Analysis**: Get intelligent insights into code quality issues
- **Issue Detection**: Identify code smells, security vulnerabilities, and performance bottlenecks
- **Best Practices**: Receive suggestions for coding standards and best practices
- **Severity Levels**: Categorized feedback (info, warning, error)

### 🎨 Modern Interface
- **Clean Design**: Intuitive and responsive user interface
- **Dark/Light Theme**: Toggle between themes for comfortable viewing
- **Real-time Preview**: See generated documentation instantly
- **Drag & Drop**: Easy file upload with drag-and-drop support

## Getting Started

### Prerequisites

- Modern web browser (Chrome, Firefox, Safari, Edge)
- For GitHub integration: GitHub Personal Access Token with `repo` scope
- For AI analysis: Gemini API key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/tekshila.git
   cd tekshila
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_API_URL=https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent
   ```

4. **Run the application**
   ```bash
   npm run dev
   ```

5. **Access the application**
   Open your browser and navigate to `http://localhost:3000`

## Usage

### Generating Documentation

1. **Upload Your Code**
   - Click the upload zone or drag files directly
   - Choose between README or Comments generation
   - Support for individual files or ZIP archives

2. **Configure Settings**
   - Enter your project name
   - Add custom instructions for specific requirements
   - Select the type of documentation needed

3. **Generate and Preview**
   - Click "Generate Documentation"
   - Review the AI-generated content in the preview panel
   - Copy or download the results

### GitHub Integration

1. **Connect to GitHub**
   - Navigate to the GitHub tab
   - Enter your Personal Access Token
   - Select repository and branch

2. **Create Pull Request**
   - Generate documentation first
   - Fill in PR title and description
   - Create pull request with generated content

### Code Quality Analysis

1. **Upload Single File**
   - Use the Quality Analysis tab
   - Upload one file for detailed analysis

2. **Review Results**
   - See categorized issues and suggestions
   - Get recommendations for improvements
   - Understand code quality metrics

## File Structure

```
tekshila/
├── frontend/
│   ├── index.html          # Main HTML file
│   ├── styles.css          # Application styles
│   ├── script.js           # Frontend JavaScript
│   └── package.json        # Frontend dependencies
├── backend/
│   ├── src/
│   │   ├── main.py         # Main backend application
│   │   ├── core.py         # Core functionality
│   │   └── api-bridge.py   # API integration
│   └── utils/
│       ├── code_quality.py    # Code quality analysis
│       └── github_integration.py  # GitHub API integration
├── requirements.txt        # Python dependencies
├── package.json           # Project metadata
└── README.md             # This file
```

## API Integration

### Gemini AI
The application uses Google's Gemini API for:
- Code analysis and understanding
- Documentation generation
- Quality assessment and suggestions

### GitHub API
GitHub integration provides:
- Repository access and management
- Branch operations
- Pull request creation
- File operations

## Configuration

### Environment Variables
- `GEMINI_API_KEY`: Your Gemini API key for AI functionality
- `GEMINI_API_URL`: Gemini API endpoint URL

### GitHub Token Setup
1. Go to GitHub Settings > Developer settings > Personal access tokens
2. Generate a new token with `repo` scope
3. Use the token in the GitHub integration tab

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please:
- Open an issue on GitHub
- Check the documentation
- Review existing issues and discussions

## Roadmap

- [ ] Support for more programming languages
- [ ] Integration with other version control systems
- [ ] Advanced code metrics and analytics
- [ ] Team collaboration features
- [ ] API for programmatic access

## Acknowledgments

- Google Gemini for AI capabilities
- GitHub for repository integration
- The open-source community for inspiration and tools

---

Made with ❤️ by the Tekshila Team
