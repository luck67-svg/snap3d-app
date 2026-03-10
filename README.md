# Snap3D - AI Powered Image to 3D Model Generator

**Snap3D** is a lightweight, AI-powered application that transforms 2D images into 3D models. Built with **Python** and **Streamlit**, it leverages powerful external AI APIs (like Meshy and Tripo) to provide a seamless "Image-to-3D" generation experience.

## ✨ Demo & Gallery

### 🎨 Cyberpunk UI Interface
> *A modern, dark-themed interface designed for immersion.*

![Snap3D UI Screenshot](assets/ui_screenshot.gif)

### 🧊 3D Generation Examples
> *From 2D Concept to 3D Asset in seconds.*

| Input Image (2D) | Generated 3D Model (Preview) |
| :---: | :---: |
| ![Input Example 1](assets/example_input_1.png) | ![Output Model 1](assets/example_output_1.gif) |

## 🚀 Features

*   **Instant 3D Generation**: Convert 2D images into 3D assets in less than a minute.
*   **Interactive 3D Viewer**: Preview generated models directly in the browser using Google's `<model-viewer>`.
*   **Multiple Formats**: Supports downloading models in GLB (for web/AR) and potentially STL (for 3D printing) formats.
*   **Cyberpunk UI**: A custom-styled, modern user interface for an immersive experience.
*   **No GPU Required**: Runs on local CPU as the heavy lifting is done by cloud AI services.

## 🛠️ Technical Architecture

Snap3D follows a **Lightweight Monolithic** architecture:

*   **Frontend/Backend**: Streamlit (Python)
*   **Image Processing**: Pillow (PIL)
*   **3D Rendering**: Web Component (`<model-viewer>`)
*   **AI Services**: Integrated with Meshy/Tripo APIs via RESTful calls.

## 📦 Installation & Setup

### Prerequisites

*   Python 3.9 or higher installed.
*   API Key for Meshy or Tripo (Get one from their respective developer portals).

### Steps

1.  **Clone the repository**
    ```bash
    git clone <your-repo-url>
    cd Snap3D
    ```

2.  **Create a virtual environment**
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Secrets**
    Copy the example secrets file:
    ```bash
    cp .streamlit/secrets.toml.example .streamlit/secrets.toml
    ```
    Edit the file `.streamlit/secrets.toml` and add your API keys:
    ```toml
    [meshy]
    api_key = "your_meshy_api_key_here"

    [tripo]
    api_key = "your_tripo_api_key_here"
    ```

5.  **Run the application**
    ```bash
    streamlit run app.py
    ```

## 📂 Project Structure

```
Snap3D/
├── app.py                  # Main application entry point
├── requirements.txt        # Python dependencies
├── Snap3D_Tech_Architecture.md # Detailed technical documentation
├── assets/                 # Static assets (images, demo models)
├── utils/                  # Utility modules
│   ├── image_processor.py  # Image handling logic
│   ├── meshy_api.py        # Meshy API client
│   └── tripo_api.py        # Tripo API client
└── .streamlit/             # Streamlit configuration
    └── config.toml         # UI theming and settings
```

## 🔮 Roadmap

*   **Phase 1**: Robustness improvements (Auto-repair meshes).
*   **Phase 2**: Performance optimization (Async task queues).
*   **Phase 3**: Production deployment & Commercialization.

---
run conmmand:
