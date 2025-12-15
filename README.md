<a id="readme-top"></a>

<!-- [![Contributors][contributors-shield]][contributors-url] -->
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]
<!-- [![LinkedIn][linkedin-shield]][linkedin-url] -->


<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/CoralShades/acm-ai">
    <img src="docs/assets/hero.svg" alt="Logo">
  </a>

  <h3 align="center">ACM-AI</h3>

  <p align="center">
    Intelligent Asbestos Compliance Management powered by AI
    <br /><strong>Built on <a href="https://github.com/lfnovo/open-notebook">Open Notebook</a> - The privacy-focused research platform</strong>
    <br />
    <br />
    <a href="docs/acm-ai/03-prd.md">📋 Product Requirements</a>
    ·
    <a href="docs/getting-started/index.md">📚 Get Started</a>
    ·
    <a href="docs/acm-ai/04-architecture.md">🏗️ Architecture</a>
    ·
    <a href="docs/deployment/index.md">🚀 Deploy</a>
  </p>
</div>

<p align="center">
<a href="https://trendshift.io/repositories/14536" target="_blank"><img src="https://trendshift.io/api/badge/repositories/14536" alt="lfnovo%2Fopen-notebook | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>
</p>

<div align="center">
  <!-- Keep these links. Translations will automatically update with the README. -->
  <a href="https://zdoc.app/de/lfnovo/open-notebook">Deutsch</a> | 
  <a href="https://zdoc.app/es/lfnovo/open-notebook">Español</a> | 
  <a href="https://zdoc.app/fr/lfnovo/open-notebook">français</a> | 
  <a href="https://zdoc.app/ja/lfnovo/open-notebook">日本語</a> | 
  <a href="https://zdoc.app/ko/lfnovo/open-notebook">한국어</a> | 
  <a href="https://zdoc.app/pt/lfnovo/open-notebook">Português</a> | 
  <a href="https://zdoc.app/ru/lfnovo/open-notebook">Русский</a> | 
  <a href="https://zdoc.app/zh/lfnovo/open-notebook">中文</a>
</div>

## Intelligent ACM Compliance Document Management with AI-Powered Analysis

![ACM-AI Platform](docs/assets/asset_list.png)

**ACM-AI transforms Asbestos Containing Material (ACM) compliance management by combining:**
- 🏛️ **SAMP Document Processing** - Automated extraction from School Asbestos Management Plans
- 📊 **Intelligent Data Extraction** - Parse hierarchical structures (School → Building → Room → ACM Item)
- 🔍 **AI-Powered Search** - Query ACM registers with natural language
- 📄 **Citation Tracking** - Every data point linked to source PDF page numbers
- 🤖 **Multi-Model AI** - Choose from 16+ providers for privacy and cost control

**Built on Open Notebook's proven foundation:**
- 🔒 **100% Private** - All document processing happens locally
- 🎯 **Multi-Provider AI** - OpenAI, Anthropic, Ollama, LM Studio, and more
- 📚 **Robust Architecture** - Battle-tested research platform powering ACM workflows

> **Note:** ACM-AI is a specialized fork of [Open Notebook](https://github.com/lfnovo/open-notebook) by [Luis Novo](https://github.com/lfnovo), focused on asbestos compliance management. All credit for the core platform goes to the Open Notebook project.

---

## ⚠️ IMPORTANT: v1.0 Breaking Changes

**If you're upgrading from a previous version**, please note:

- 🏷️ **Docker tags have changed**: The `latest` tag is now **frozen** at the last Streamlit version
- 🆕 **Use `v1-latest` tag** for the new React/Next.js version (recommended)
- 🔌 **Port 5055 required**: You must expose port 5055 for the API to work
- 📖 **Read the migration guide**: See [MIGRATION.md](MIGRATION.md) for detailed upgrade instructions

**New users**: You can ignore this notice and proceed with the Quick Start below using the `v1-latest-single` tag.

---

## 🎯 Why ACM-AI?

**Transform Your Asbestos Compliance Management:**

| Challenge | Traditional Approach | ACM-AI Solution |
|-----------|---------------------|-----------------|
| **Data Entry** | Manual transcription from PDFs | Automated extraction with 90%+ accuracy |
| **Document Search** | Ctrl+F through individual PDFs | AI-powered natural language queries |
| **Data Validation** | Manual cross-checking across pages | Hierarchical structure validation |
| **Citation Tracking** | Manual page references | Automatic source linking to PDF pages |
| **Report Generation** | Copy-paste from multiple documents | Query and export structured data |
| **Cost** | Hours of manual labor | Minutes of AI processing |

**Key Benefits:**
- 📊 **Structured Data**: Transform unstructured PDFs into queryable database records
- 🏗️ **Hierarchical Tracking**: Maintain School → Building → Room → ACM Item relationships
- 🔍 **Intelligent Search**: "Show all asbestos in Science Block built before 1980"
- 📄 **Audit Trail**: Every extracted record links to source PDF and page number
- 🤖 **Multi-Model AI**: Choose from 16+ providers for cost optimization
- 🔒 **Privacy First**: All processing happens locally on your infrastructure

### Built With

[![Python][Python]][Python-url] [![Next.js][Next.js]][Next-url] [![React][React]][React-url] [![SurrealDB][SurrealDB]][SurrealDB-url] [![LangChain][LangChain]][LangChain-url]

## 🚀 Quick Start

**ACM-AI Setup:**

ACM-AI uses the same Docker deployment as Open Notebook, with specialized ACM extraction capabilities built in. The setup is identical - just configure your AI provider and start processing ACM documents!

**Docker Images Available:**
- **Docker Hub**: `lfnovo/open_notebook:v1-latest-single` (ACM-AI compatible)
- **GitHub Container Registry**: `ghcr.io/lfnovo/open-notebook:v1-latest-single`

> **Note:** ACM-AI is a code fork - use the Open Notebook images for now. Custom ACM-AI Docker images coming soon!

### Choose Your Setup:

<table>
<tr>
<td width="50%">

#### 🏠 **Local Machine Setup**
Perfect if Docker runs on the **same computer** where you'll access Open Notebook.

```bash
mkdir open-notebook && cd open-notebook

docker run -d \
  --name open-notebook \
  -p 8502:8502 -p 5055:5055 \
  -v ./notebook_data:/app/data \
  -v ./surreal_data:/mydata \
  -e OPENAI_API_KEY=your_key_here \
  -e SURREAL_URL="ws://localhost:8000/rpc" \
  -e SURREAL_USER="root" \
  -e SURREAL_PASSWORD="root" \
  -e SURREAL_NAMESPACE="open_notebook" \
  -e SURREAL_DATABASE="production" \
  lfnovo/open_notebook:v1-latest-single
```

**Access at:** http://localhost:8502

</td>
<td width="50%">

#### 🌐 **Remote Server Setup**
Use this for servers, Raspberry Pi, NAS, Proxmox, or any remote machine.

```bash
mkdir open-notebook && cd open-notebook

docker run -d \
  --name open-notebook \
  -p 8502:8502 -p 5055:5055 \
  -v ./notebook_data:/app/data \
  -v ./surreal_data:/mydata \
  -e OPENAI_API_KEY=your_key_here \
  -e API_URL=http://YOUR_SERVER_IP:5055 \
  -e SURREAL_URL="ws://localhost:8000/rpc" \
  -e SURREAL_USER="root" \
  -e SURREAL_PASSWORD="root" \
  -e SURREAL_NAMESPACE="open_notebook" \
  -e SURREAL_DATABASE="production" \
  lfnovo/open_notebook:v1-latest-single
```

**Replace `YOUR_SERVER_IP`** with your server's IP (e.g., `192.168.1.100`) or domain

**Access at:** http://YOUR_SERVER_IP:8502

</td>
</tr>
</table>

> **⚠️ Critical Setup Notes:**
>
> **Both ports are required:**
> - **Port 8502**: Web interface (what you see in your browser)
> - **Port 5055**: API backend (required for the app to function)
>
> **API_URL must match how YOU access the server:**
> - ✅ Access via `http://192.168.1.100:8502` → set `API_URL=http://192.168.1.100:5055`
> - ✅ Access via `http://myserver.local:8502` → set `API_URL=http://myserver.local:5055`
> - ❌ Don't use `localhost` for remote servers - it won't work from other devices!

### Using Docker Compose (Recommended for Easy Management)

Create a `docker-compose.yml` file:

```yaml
services:
  open_notebook:
    image: lfnovo/open_notebook:v1-latest-single
    # Or use: ghcr.io/lfnovo/open-notebook:v1-latest-single
    ports:
      - "8502:8502"  # Web UI
      - "5055:5055"  # API (required!)
    environment:
      - OPENAI_API_KEY=your_key_here
      # For remote access, uncomment and set your server IP/domain:
      # - API_URL=http://192.168.1.100:5055
      # Database connection (required for single-container)
      - SURREAL_URL=ws://localhost:8000/rpc
      - SURREAL_USER=root
      - SURREAL_PASSWORD=root
      - SURREAL_NAMESPACE=open_notebook
      - SURREAL_DATABASE=production
    volumes:
      - ./notebook_data:/app/data
      - ./surreal_data:/mydata
    restart: always
```

Start with: `docker compose up -d`

**What gets created:**
```
open-notebook/
├── docker-compose.yml # Your configuration
├── notebook_data/     # Your notebooks and research content
└── surreal_data/      # Database files
```

### 🆘 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| **"Unable to connect to server"** | Set `API_URL` environment variable to match how you access the server (see remote setup above) |
| **Blank page or errors** | Ensure BOTH ports (8502 and 5055) are exposed in your docker command |
| **Works on server but not from other computers** | Don't use `localhost` in `API_URL` - use your server's actual IP address |
| **"404" or "config endpoint" errors** | Don't add `/api` to `API_URL` - use just `http://your-ip:5055` |
| **Still having issues?** | Check our [5-minute troubleshooting guide](docs/troubleshooting/quick-fixes.md) or [join Discord](https://discord.gg/37XJPXfz2w) |

### How Open Notebook Works

```
┌─────────────────────────────────────────────────────────┐
│  Your Browser                                           │
│  Access: http://your-server-ip:8502                     │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
         ┌───────────────┐
         │   Port 8502   │  ← Next.js Frontend (what you see)
         │   Frontend    │    Also proxies API requests internally!
         └───────┬───────┘
                 │ proxies /api/* requests ↓
                 ▼
         ┌───────────────┐
         │   Port 5055   │  ← FastAPI Backend (handles requests)
         │     API       │
         └───────┬───────┘
                 │
                 ▼
         ┌───────────────┐
         │   SurrealDB   │  ← Database (internal, auto-configured)
         │   (Port 8000) │
         └───────────────┘
```

**Key Points:**
- **v1.1+**: Next.js automatically proxies `/api/*` requests to the backend, simplifying reverse proxy setup
- Your browser loads the frontend from port 8502
- The frontend needs to know where to find the API - when accessing remotely, set: `API_URL=http://your-server-ip:5055`
- **Behind reverse proxy?** You only need to proxy to port 8502 now! See [Reverse Proxy Guide](docs/deployment/reverse-proxy.md)

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=lfnovo/open-notebook&type=date&legend=top-left)](https://www.star-history.com/#lfnovo/open-notebook&type=date&legend=top-left)

### 🛠️ Full Installation
For development or customization:
```bash
git clone https://github.com/lfnovo/open-notebook
cd open-notebook
make start-all
```

### 📖 Need Help?
- **🤖 AI Installation Assistant**: We have a [CustomGPT built to help you install Open Notebook](https://chatgpt.com/g/g-68776e2765b48191bd1bae3f30212631-open-notebook-installation-assistant) - it will guide you through each step!
- **New to Open Notebook?** Start with our [Getting Started Guide](docs/getting-started/index.md)
- **Need installation help?** Check our [Installation Guide](docs/getting-started/installation.md)
- **Want to see it in action?** Try our [Quick Start Tutorial](docs/getting-started/quick-start.md)

## Provider Support Matrix

Thanks to the [Esperanto](https://github.com/lfnovo/esperanto) library, we support this providers out of the box!

| Provider     | LLM Support | Embedding Support | Speech-to-Text | Text-to-Speech |
|--------------|-------------|------------------|----------------|----------------|
| OpenAI       | ✅          | ✅               | ✅             | ✅             |
| Anthropic    | ✅          | ❌               | ❌             | ❌             |
| Groq         | ✅          | ❌               | ✅             | ❌             |
| Google (GenAI) | ✅          | ✅               | ❌             | ✅             |
| Vertex AI    | ✅          | ✅               | ❌             | ✅             |
| Ollama       | ✅          | ✅               | ❌             | ❌             |
| Perplexity   | ✅          | ❌               | ❌             | ❌             |
| ElevenLabs   | ❌          | ❌               | ✅             | ✅             |
| Azure OpenAI | ✅          | ✅               | ❌             | ❌             |
| Mistral      | ✅          | ✅               | ❌             | ❌             |
| DeepSeek     | ✅          | ❌               | ❌             | ❌             |
| Voyage       | ❌          | ✅               | ❌             | ❌             |
| xAI          | ✅          | ❌               | ❌             | ❌             |
| OpenRouter   | ✅          | ❌               | ❌             | ❌             |
| OpenAI Compatible* | ✅          | ❌               | ❌             | ❌             |

*Supports LM Studio and any OpenAI-compatible endpoint

## ✨ Key Features

### ACM-Specific Capabilities
- **📄 SAMP Document Processing**: Automated extraction from School Asbestos Management Plans
- **🏗️ Hierarchical Data Structure**: School → Building → Room → ACM Item relationships
- **🎯 Smart Pattern Recognition**: Detects building IDs, room codes, area types automatically
- **📊 Structured Database**: Transform PDFs into queryable ACMRecord objects
- **🔍 Field-Level Extraction**: Product, material description, friable status, risk, condition, extent
- **📍 Citation Tracking**: Every record links to source document and page number
- **🤖 Background Processing**: Async extraction with retry logic and error handling
- **✅ High Accuracy**: 90%+ field accuracy on real-world ACM registers

### AI-Powered Intelligence
- **🤖 Multi-Model Support**: 16+ providers including OpenAI, Anthropic, Ollama, Google, LM Studio
- **💬 Natural Language Queries**: "Show all friable asbestos in buildings before 1980"
- **🔍 Semantic Search**: Vector search across ACM descriptions and locations
- **📝 AI-Assisted Analysis**: Generate compliance reports and risk summaries
- **⚡ Reasoning Models**: Full support for thinking models like DeepSeek-R1

### Built on Open Notebook Foundation
- **🔒 Privacy-First**: Your sensitive compliance data stays under your control
- **🎯 Multi-Notebook Organization**: Manage multiple school districts or properties
- **📚 Universal Content Support**: PDFs, Office docs, web pages, and more
- **🌐 Comprehensive REST API**: Full programmatic access [![API Docs](https://img.shields.io/badge/API-Documentation-blue?style=flat-square)](http://localhost:5055/docs)
- **🔐 Optional Password Protection**: Secure public deployments with authentication

[![Check out our podcast sample](https://img.youtube.com/vi/D-760MlGwaI/0.jpg)](https://www.youtube.com/watch?v=D-760MlGwaI)

## 📚 Documentation

### Getting Started
- **[📖 Introduction](docs/getting-started/introduction.md)** - Learn what Open Notebook offers
- **[⚡ Quick Start](docs/getting-started/quick-start.md)** - Get up and running in 5 minutes
- **[🔧 Installation](docs/getting-started/installation.md)** - Comprehensive setup guide
- **[🎯 Your First Notebook](docs/getting-started/first-notebook.md)** - Step-by-step tutorial

### User Guide
- **[📱 Interface Overview](docs/user-guide/interface-overview.md)** - Understanding the layout
- **[📚 Notebooks](docs/user-guide/notebooks.md)** - Organizing your research
- **[📄 Sources](docs/user-guide/sources.md)** - Managing content types
- **[📝 Notes](docs/user-guide/notes.md)** - Creating and managing notes
- **[💬 Chat](docs/user-guide/chat.md)** - AI conversations
- **[🔍 Search](docs/user-guide/search.md)** - Finding information

### Advanced Topics
- **[🎙️ Podcast Generation](docs/features/podcasts.md)** - Create professional podcasts
- **[🔧 Content Transformations](docs/features/transformations.md)** - Customize content processing
- **[🤖 AI Models](docs/features/ai-models.md)** - AI model configuration
- **[🔧 REST API Reference](docs/development/api-reference.md)** - Complete API documentation
- **[🔐 Security](docs/deployment/security.md)** - Password protection and privacy
- **[🚀 Deployment](docs/deployment/index.md)** - Complete deployment guides for all scenarios

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## 🗺️ Roadmap

### ACM-AI Current Status ✅
**Phase 1 - Core Extraction (COMPLETE)**
- ✅ **ACMRecord Domain Model**: Full Pydantic model with SurrealDB integration
- ✅ **ACM Extraction Engine**: Regex-based parser for Docling markdown output
- ✅ **Hierarchical Context Tracking**: School → Building → Room → Item relationships
- ✅ **Background Command Processing**: Async extraction with retry logic
- ✅ **Comprehensive Test Suite**: 47 passing tests (unit + integration)
- ✅ **High Accuracy**: 90%+ field accuracy on real ACM register samples

### Next for ACM-AI
- **Real PDF Testing**: Validate against actual 1124, 3980, 4601 SAMP PDFs
- **Frontend ACM Views**: UI components for browsing extracted ACM data
- **Export Capabilities**: CSV/Excel export for compliance reporting
- **Advanced Querying**: Natural language queries over ACM database
- **Risk Analytics**: Dashboard showing high-risk materials by building/school

### Open Notebook Foundation Features
- **Live Front-End Updates**: Real-time UI updates for smoother experience
- **Cross-Notebook Sources**: Reuse research materials across projects
- **Bookmark Integration**: Connect with your favorite bookmarking apps

See the [open issues](https://github.com/CoralShades/acm-ai/issues) for ACM-AI specific features and [Open Notebook issues](https://github.com/lfnovo/open-notebook/issues) for platform features.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## 🤝 Community & Contributing

### ACM-AI Support
- 🐛 **[GitHub Issues](https://github.com/CoralShades/acm-ai/issues)** - Report ACM-specific bugs and request features
- ⭐ **Star this repo** - Show your support and help others discover ACM-AI

### Open Notebook Community
For platform-level questions and general support:
- 💬 **[Discord Server](https://discord.gg/37XJPXfz2w)** - Get help, share ideas, and connect with other users
- 🐛 **[GitHub Issues](https://github.com/lfnovo/open-notebook/issues)** - Report platform bugs

### Contributing to ACM-AI
We welcome contributions! We're especially looking for help with:
- **ACM Extraction Improvements**: Enhance parsing accuracy and handle edge cases
- **Frontend Development**: Build ACM-specific UI components and dashboards
- **Real-world Testing**: Test with actual SAMP PDFs and report issues
- **Export & Reporting**: Add CSV/Excel export and compliance reporting features
- **Documentation**: Improve guides for ACM compliance workflows

**Current Tech Stack**: Python, FastAPI, Next.js, React, SurrealDB, Docling

See our [Contributing Guide](CONTRIBUTING.md) for detailed information on how to get started.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## 📄 License

ACM-AI is MIT licensed, inheriting the license from Open Notebook. See the [LICENSE](LICENSE) file for details.

## 📞 Contact

**ACM-AI Project**:
- 🐛 [GitHub Issues](https://github.com/CoralShades/acm-ai/issues) - Report ACM-specific bugs and request features
- 🌐 [CoralShades Organization](https://github.com/CoralShades) - View all our projects

**Open Notebook (Platform Foundation)**:
- 👨‍💻 **Luis Novo** - [@lfnovo](https://twitter.com/lfnovo)
- 💬 [Discord Server](https://discord.gg/37XJPXfz2w) - Get help and connect with the community
- 🐛 [GitHub Issues](https://github.com/lfnovo/open-notebook/issues) - Report platform bugs
- 🌐 [Website](https://www.open-notebook.ai) - Learn more about Open Notebook

## 🙏 Acknowledgments

### Built on Open Notebook
**ACM-AI is a specialized fork of [Open Notebook](https://github.com/lfnovo/open-notebook)** created by [Luis Novo](https://github.com/lfnovo).

All credit for the core platform architecture, AI workflows, and document processing infrastructure goes to the Open Notebook project and its contributors. ACM-AI adds domain-specific extraction logic for asbestos compliance management on top of this excellent foundation.

### Core Dependencies
* **[Open Notebook](https://github.com/lfnovo/open-notebook)** - Privacy-focused research platform foundation
* **[Podcast Creator](https://github.com/lfnovo/podcast-creator)** - Advanced podcast generation capabilities
* **[Surreal Commands](https://github.com/lfnovo/surreal-commands)** - Background job processing
* **[Content Core](https://github.com/lfnovo/content-core)** - Content processing and management
* **[Esperanto](https://github.com/lfnovo/esperanto)** - Multi-provider AI model abstraction
* **[Docling](https://github.com/docling-project/docling)** - Document processing and parsing

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/lfnovo/open-notebook.svg?style=for-the-badge
[contributors-url]: https://github.com/lfnovo/open-notebook/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/lfnovo/open-notebook.svg?style=for-the-badge
[forks-url]: https://github.com/lfnovo/open-notebook/network/members
[stars-shield]: https://img.shields.io/github/stars/lfnovo/open-notebook.svg?style=for-the-badge
[stars-url]: https://github.com/lfnovo/open-notebook/stargazers
[issues-shield]: https://img.shields.io/github/issues/lfnovo/open-notebook.svg?style=for-the-badge
[issues-url]: https://github.com/lfnovo/open-notebook/issues
[license-shield]: https://img.shields.io/github/license/lfnovo/open-notebook.svg?style=for-the-badge
[license-url]: https://github.com/lfnovo/open-notebook/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/lfnovo
[product-screenshot]: images/screenshot.png
[Next.js]: https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=next.js&logoColor=white
[Next-url]: https://nextjs.org/
[React]: https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black
[React-url]: https://reactjs.org/
[Python]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white
[Python-url]: https://www.python.org/
[LangChain]: https://img.shields.io/badge/LangChain-3A3A3A?style=for-the-badge&logo=chainlink&logoColor=white
[LangChain-url]: https://www.langchain.com/
[SurrealDB]: https://img.shields.io/badge/SurrealDB-FF5E00?style=for-the-badge&logo=databricks&logoColor=white
[SurrealDB-url]: https://surrealdb.com/
