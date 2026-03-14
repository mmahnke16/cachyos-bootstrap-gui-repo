# CachyOS Dev Bootstrap GUI

A modern GTK4 application to streamline the setup of a development environment on CachyOS and Arch-based Linux distributions. This tool generates and executes a tailored bootstrap script to install essential tools, AI models, and configurations.

## 🚀 Features

*   **GUI Configuration**: Easy-to-use interface to customize your setup before running.
*   **Editor Selection**: Automated installation of VS Code (OSS) or VSCodium.
*   **AI Integration**: Seamless setup of **Ollama** with model selection (Qwen, DeepSeek, etc.) and editor extensions (**Continue**, **Cline**).
*   **Terminal Detection**: Automatically detects and launches in your preferred terminal emulator (Kitty, WezTerm, Gnome Terminal, etc.).
*   **Package Groups**: One-click selection for common tech stacks:
    *   **Base**: git, curl, rsync, jq, ripgrep, etc.
    *   **Languages**: Python, Node.js, Rust, Go, Java.
    *   **Tools**: Docker, Shell enhancements (zsh, starship, zoxide).
*   **Customization**: Add your own custom pacman or AUR packages and arbitrary shell commands.
*   **Safety**: Generates a reviewable shell script before execution.

## 📋 Prerequisites

*   **OS**: CachyOS, Arch Linux, or derivatives.
*   **Python**: 3.10+
*   **GTK4**: Required for the GUI.

## 🛠️ Installation & Usage

1.  **Clone the repository**:
    `ash
    git clone <your-repo-url>
    cd cachyos-bootstrap-gui
    `

2.  **Install Dependencies**:
    Run the included script to install necessary system packages (Python, GTK4, Zenity):
    `ash
    chmod +x install-deps.sh
    ./install-deps.sh
    `

3.  **Launch the App**:
    `ash
    chmod +x launch.sh
    ./launch.sh
    `

## ⚙️ How it Works

The application does not make changes immediately. Instead, it:
1.  **Generates** a shell script based on your selections at ~/.config/cachyos-dev-bootstrap/run-bootstrap.sh.
2.  **Saves** your configuration to ~/.config/cachyos-dev-bootstrap/last-config.json for future runs.
3.  **Executes** the generated script in a new terminal window to handle sudo prompts and display progress.

## 📂 Project Structure

*   ootstrap_gui.py: The main Python GTK4 application.
*   install-deps.sh: Helper script to install runtime dependencies.
*   launch.sh: Wrapper to start the application.

## 🔧 Troubleshooting

*   **Ollama**: If installed, the default endpoint is http://localhost:11434.
*   **Terminals**: If the app fails to launch the terminal, check the logs or run the generated script manually from the path above.

## 📄 License

[MIT](LICENSE)
