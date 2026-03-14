#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path

import gi

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio, GLib

APP_ID = 'com.mysticalmahnke.CachyOSBootstrap'
CONFIG_DIR = Path.home() / '.config' / 'cachyos-dev-bootstrap'
SCRIPT_PATH = CONFIG_DIR / 'run-bootstrap.sh'
CONFIG_PATH = CONFIG_DIR / 'last-config.json'
LOG_PATH = CONFIG_DIR / 'bootstrap.log'
DESKTOP_PATH = Path.home() / '.local/share/applications/cachyos-dev-bootstrap.desktop'

EDITOR_OPTIONS = [
    ('code', 'Code - OSS (repo)'),
    ('vscodium-bin', 'VSCodium (AUR)'),
    ('skip', 'Skip editor install'),
]
MODEL_OPTIONS = [
    ('qwen2.5-coder:7b', 'qwen2.5-coder:7b'),
    ('qwen2.5-coder:14b', 'qwen2.5-coder:14b'),
    ('deepseek-coder-v2:16b', 'deepseek-coder-v2:16b'),
    ('skip', 'Skip model pull'),
]
TERMINALS = [
    ('auto', 'Auto detect'),
    ('kitty', 'kitty'),
    ('wezterm', 'wezterm'),
    ('gnome-terminal', 'gnome-terminal'),
    ('konsole', 'konsole'),
    ('xfce4-terminal', 'xfce4-terminal'),
    ('alacritty', 'alacritty'),
    ('foot', 'foot'),
    ('xterm', 'xterm'),
]

PKG_GROUPS = {
    'base': ['base-devel', 'git', 'curl', 'wget', 'unzip', 'zip', 'tar', 'openssh', 'rsync', 'jq', 'tree', 'ripgrep', 'fd', 'fzf', 'bat', 'eza', 'neovim', 'tmux', 'github-cli', 'zenity', 'python'],
    'python': ['python-pip', 'uv'],
    'node': ['nodejs', 'npm'],
    'rust': ['rustup'],
    'go': ['go'],
    'java': ['jdk-openjdk'],
    'docker': ['docker', 'docker-compose'],
    'shell': ['zsh', 'starship', 'zoxide', 'fastfetch'],
    'dev': ['python-pytest', 'bandit', 'shellcheck'],
}

AUR_HINTS = ['paru', 'cursor-bin', 'fnm', 'vscodium-bin']
EXTENSIONS = {
    'continue': 'Continue.continue',
    'cline': 'saoudrizwan.claude-dev',
}


@dataclass
class AppConfig:
    editor: str = 'code'
    model: str = 'qwen2.5-coder:7b'
    terminal: str = 'auto'
    install_ollama: bool = True
    install_continue: bool = True
    install_cline: bool = False
    groups: dict | None = None
    extra_pacman: str = ''
    extra_aur: str = ''
    extra_commands: str = ''

    def __post_init__(self):
        if self.groups is None:
            self.groups = {k: (k in {'base', 'python', 'node', 'shell'}) for k in PKG_GROUPS}


def generate_bootstrap_script(cfg: AppConfig) -> str:
    pacman_pkgs = []
    for group, enabled in cfg.groups.items():
        if enabled:
            pacman_pkgs.extend(PKG_GROUPS[group])
    if cfg.editor == 'code':
        pacman_pkgs.append('code')
    if cfg.extra_pacman:
        pacman_pkgs.extend(cfg.extra_pacman.split())
    pacman_pkgs = sorted(dict.fromkeys(pacman_pkgs))

    aur_pkgs = []
    if cfg.editor == 'vscodium-bin':
        aur_pkgs.append('vscodium-bin')
    if cfg.extra_aur:
        aur_pkgs.extend(cfg.extra_aur.split())
    aur_pkgs = sorted(dict.fromkeys(aur_pkgs))

    ext_lines = []
    if cfg.install_continue:
        ext_lines.append(f'install_extension "{EXTENSIONS["continue"]}"')
    if cfg.install_cline:
        ext_lines.append(f'install_extension "{EXTENSIONS["cline"]}"')
    ext_block = '\n'.join(ext_lines) if ext_lines else 'echo "No editor extensions selected."'

    model_block = ''
    if cfg.install_ollama and cfg.model != 'skip':
        model_block = f'ollama pull {shlex.quote(cfg.model)}\n'

    extra_cmds = cfg.extra_commands.strip()
    if not extra_cmds:
        extra_cmds = 'echo "No extra post-install commands."'

    return f'''#!/usr/bin/env bash
set -euo pipefail

CONFIG_DIR={shlex.quote(str(CONFIG_DIR))}
LOG_FILE={shlex.quote(str(LOG_PATH))}
mkdir -p "$CONFIG_DIR"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "==> Updating system"
sudo pacman -Syu --noconfirm

have_cmd() {{ command -v "$1" >/dev/null 2>&1; }}

ensure_paru() {{
  if have_cmd paru; then return; fi
  echo "==> Installing paru"
  sudo pacman -S --needed --noconfirm paru
}}

install_extension() {{
  local ext="$1"
  if have_cmd code; then
    code --install-extension "$ext" || true
  elif have_cmd codium; then
    codium --install-extension "$ext" || true
  else
    echo "No code/codium binary found; skipping $ext"
  fi
}}

echo "==> Installing pacman packages"
sudo pacman -S --needed --noconfirm {' '.join(shlex.quote(x) for x in pacman_pkgs)}

if {'true' if aur_pkgs else 'false'}; then
  ensure_paru
  echo "==> Installing AUR packages"
  paru -S --needed --noconfirm {' '.join(shlex.quote(x) for x in aur_pkgs) if aur_pkgs else ''}
fi

{'echo "==> Installing Ollama"\nif ! have_cmd ollama; then\n  curl -fsSL https://ollama.com/install.sh | sh\nfi\nif systemctl list-unit-files | grep -q "^ollama.service"; then\n  sudo systemctl enable --now ollama\nelse\n  systemctl --user enable --now ollama || true\nfi\n' if cfg.install_ollama else 'echo "Skipping Ollama install"\n'}

{'echo "==> Pulling starter model"\n' + model_block if model_block else 'echo "Skipping model pull"\n'}

echo "==> Runtime setup"
mkdir -p "$HOME/.local/bin" "$HOME/code" "$HOME/projects" "$HOME/bin" "$HOME/tmp"
if have_cmd rustup; then rustup default stable || true; fi
if have_cmd docker; then sudo systemctl enable --now docker || true; sudo usermod -aG docker "$USER" || true; fi

echo "==> Installing selected editor extensions"
{ext_block}

echo "==> Writing shell hints"
grep -qxF 'export PATH="$HOME/.local/bin:$PATH"' "$HOME/.bashrc" || echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
if [ -f "$HOME/.zshrc" ] || have_cmd zsh; then
  touch "$HOME/.zshrc"
  grep -qxF 'export PATH="$HOME/.local/bin:$PATH"' "$HOME/.zshrc" || echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc"
  grep -qxF 'eval "$(starship init zsh)"' "$HOME/.zshrc" || echo 'eval "$(starship init zsh)"' >> "$HOME/.zshrc" || true
  grep -qxF 'eval "$(zoxide init zsh)"' "$HOME/.zshrc" || echo 'eval "$(zoxide init zsh)"' >> "$HOME/.zshrc" || true
fi

echo "==> Running extra post-install commands"
{extra_cmds}

echo "==> Done"
echo "Log: $LOG_FILE"
echo "If Ollama is installed, endpoint is usually http://localhost:11434"
'''


class BootstrapWindow(Gtk.ApplicationWindow):
    def __init__(self, app: Gtk.Application):
        super().__init__(application=app)
        self.set_title('CachyOS Dev Bootstrap')
        self.set_default_size(980, 780)

        self.config = self.load_config()

        header = Gtk.HeaderBar()
        header.set_show_title_buttons(True)
        self.set_titlebar(header)

        self.status_label = Gtk.Label(label='Ready')
        header.pack_start(self.status_label)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        root.set_margin_top(12)
        root.set_margin_bottom(12)
        root.set_margin_start(12)
        root.set_margin_end(12)
        self.set_child(root)

        toolbar = Gtk.Box(spacing=8)
        root.append(toolbar)

        self.generate_btn = Gtk.Button(label='Generate script')
        self.generate_btn.connect('clicked', self.on_generate)
        toolbar.append(self.generate_btn)

        self.run_btn = Gtk.Button(label='Run bootstrap')
        self.run_btn.connect('clicked', self.on_run)
        toolbar.append(self.run_btn)

        self.desktop_btn = Gtk.Button(label='Install desktop launcher')
        self.desktop_btn.connect('clicked', self.on_install_desktop)
        toolbar.append(self.desktop_btn)

        self.health_btn = Gtk.Button(label='Health check')
        self.health_btn.connect('clicked', self.on_health_check)
        toolbar.append(self.health_btn)

        paned = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)
        paned.set_wide_handle(True)
        root.append(paned)

        left_scroller = Gtk.ScrolledWindow()
        left_scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        paned.set_start_child(left_scroller)

        form = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        left_scroller.set_child(form)

        form.append(self.section_label('Core choices'))

        self.editor_combo = self.make_combo(EDITOR_OPTIONS, self.config.editor)
        form.append(self.row('Editor', self.editor_combo))

        self.model_combo = self.make_combo(MODEL_OPTIONS, self.config.model)
        form.append(self.row('Starter model', self.model_combo))

        self.terminal_combo = self.make_combo(TERMINALS, self.config.terminal)
        form.append(self.row('Terminal', self.terminal_combo))

        self.install_ollama_switch = Gtk.Switch(active=self.config.install_ollama)
        form.append(self.row('Install Ollama', self.install_ollama_switch))

        form.append(self.section_label('Extensions'))
        self.continue_switch = Gtk.Switch(active=self.config.install_continue)
        form.append(self.row('Install Continue', self.continue_switch))
        self.cline_switch = Gtk.Switch(active=self.config.install_cline)
        form.append(self.row('Install Cline', self.cline_switch))

        form.append(self.section_label('Package groups'))
        self.group_switches = {}
        for key in PKG_GROUPS:
            sw = Gtk.Switch(active=bool(self.config.groups.get(key, False)))
            self.group_switches[key] = sw
            form.append(self.row(f'{key} ({", ".join(PKG_GROUPS[key][:4])}...)', sw))

        form.append(self.section_label('Custom additions'))
        self.extra_pacman = self.make_textview(self.config.extra_pacman, 'extra pacman packages, space separated')
        form.append(self.text_block('Extra pacman packages', self.extra_pacman))
        self.extra_aur = self.make_textview(self.config.extra_aur, 'extra AUR packages, space separated')
        form.append(self.text_block('Extra AUR packages', self.extra_aur))
        self.extra_cmds = self.make_textview(self.config.extra_commands, 'one shell command per line')
        form.append(self.text_block('Extra post-install commands', self.extra_cmds))

        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        paned.set_end_child(right_box)

        right_box.append(self.section_label('Generated bootstrap script'))
        self.script_view = Gtk.TextView(editable=False, monospace=True)
        self.script_view.set_vexpand(True)
        script_scroll = Gtk.ScrolledWindow()
        script_scroll.set_child(self.script_view)
        right_box.append(script_scroll)

        right_box.append(self.section_label('Output / health'))
        self.output_view = Gtk.TextView(editable=False, monospace=True)
        self.output_view.set_vexpand(True)
        out_scroll = Gtk.ScrolledWindow()
        out_scroll.set_child(self.output_view)
        right_box.append(out_scroll)

        self.refresh_preview()

    def section_label(self, text: str) -> Gtk.Label:
        lbl = Gtk.Label(label=f'<b>{GLib.markup_escape_text(text)}</b>', use_markup=True, xalign=0)
        return lbl

    def row(self, label: str, widget: Gtk.Widget) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        box.set_hexpand(True)
        lbl = Gtk.Label(label=label, xalign=0)
        lbl.set_hexpand(True)
        box.append(lbl)
        box.append(widget)
        return box

    def text_block(self, label: str, widget: Gtk.Widget) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.append(Gtk.Label(label=label, xalign=0))
        box.append(widget)
        return box

    def make_textview(self, initial: str, placeholder: str) -> Gtk.ScrolledWindow:
        tv = Gtk.TextView()
        tv.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        tv.set_monospace(True)
        buf = tv.get_buffer()
        buf.set_text(initial)
        tv.set_tooltip_text(placeholder)
        sw = Gtk.ScrolledWindow()
        sw.set_min_content_height(80)
        sw.set_child(tv)
        sw._inner = tv
        return sw

    def get_textview_text(self, sw: Gtk.ScrolledWindow) -> str:
        tv = sw._inner
        buf = tv.get_buffer()
        start, end = buf.get_bounds()
        return buf.get_text(start, end, True).strip()

    def make_combo(self, options, current: str) -> Gtk.DropDown:
        labels = [label for _, label in options]
        model = Gtk.StringList.new(labels)
        combo = Gtk.DropDown(model=model)
        idx = 0
        for i, (value, _) in enumerate(options):
            if value == current:
                idx = i
                break
        combo.set_selected(idx)
        combo._options = options
        return combo

    def combo_value(self, combo: Gtk.DropDown) -> str:
        return combo._options[combo.get_selected()][0]

    def gather(self) -> AppConfig:
        cfg = AppConfig(
            editor=self.combo_value(self.editor_combo),
            model=self.combo_value(self.model_combo),
            terminal=self.combo_value(self.terminal_combo),
            install_ollama=self.install_ollama_switch.get_active(),
            install_continue=self.continue_switch.get_active(),
            install_cline=self.cline_switch.get_active(),
            groups={k: sw.get_active() for k, sw in self.group_switches.items()},
            extra_pacman=self.get_textview_text(self.extra_pacman),
            extra_aur=self.get_textview_text(self.extra_aur),
            extra_commands=self.get_textview_text(self.extra_cmds),
        )
        return cfg

    def refresh_preview(self):
        script = generate_bootstrap_script(self.gather())
        self.set_textview(self.script_view, script)

    def set_textview(self, view: Gtk.TextView, text: str):
        buf = view.get_buffer()
        buf.set_text(text)

    def append_output(self, text: str):
        buf = self.output_view.get_buffer()
        old = buf.get_text(*buf.get_bounds(), True)
        buf.set_text((old + ('\n' if old else '') + text).strip())

    def on_generate(self, *_args):
        cfg = self.gather()
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        script = generate_bootstrap_script(cfg)
        SCRIPT_PATH.write_text(script, encoding='utf-8')
        os.chmod(SCRIPT_PATH, 0o755)
        CONFIG_PATH.write_text(json.dumps(cfg.__dict__, indent=2), encoding='utf-8')
        self.refresh_preview()
        self.status_label.set_label('Script generated')
        self.append_output(f'Generated: {SCRIPT_PATH}')

    def terminal_command(self, script_path: Path, terminal_choice: str):
        terminals = []
        if terminal_choice != 'auto':
            terminals = [terminal_choice]
        else:
            terminals = ['kitty', 'wezterm', 'gnome-terminal', 'konsole', 'xfce4-terminal', 'alacritty', 'foot', 'xterm']
        for term in terminals:
            if shutil_which(term):
                if term == 'kitty':
                    return [term, 'bash', '-lc', f'{shlex.quote(str(script_path))}; echo; read -n 1 -s -r -p "Press any key to close..."']
                if term == 'wezterm':
                    return [term, 'start', '--always-new-process', 'bash', '-lc', f'{shlex.quote(str(script_path))}; echo; read -n 1 -s -r -p "Press any key to close..."']
                if term == 'gnome-terminal':
                    return [term, '--', 'bash', '-lc', f'{shlex.quote(str(script_path))}; echo; read -n 1 -s -r -p "Press any key to close..."']
                if term == 'konsole':
                    return [term, '-e', 'bash', '-lc', f'{shlex.quote(str(script_path))}; echo; read -n 1 -s -r -p "Press any key to close..."']
                if term == 'xfce4-terminal':
                    return [term, '--hold', '-e', f'bash -lc {shlex.quote(str(script_path) + "; echo; read -n 1 -s -r -p \'Press any key to close...\'") }']
                if term == 'alacritty':
                    return [term, '-e', 'bash', '-lc', f'{shlex.quote(str(script_path))}; echo; read -n 1 -s -r -p "Press any key to close..."']
                if term == 'foot':
                    return [term, 'bash', '-lc', f'{shlex.quote(str(script_path))}; echo; read -n 1 -s -r -p "Press any key to close..."']
                if term == 'xterm':
                    return [term, '-hold', '-e', 'bash', '-lc', str(script_path)]
        return None

    def on_run(self, *_args):
        self.on_generate()
        cfg = self.gather()
        cmd = self.terminal_command(SCRIPT_PATH, cfg.terminal)
        if cmd is None:
            self.append_output('No supported terminal emulator detected. Run this manually:\n' + str(SCRIPT_PATH))
            self.status_label.set_label('No terminal found')
            return
        try:
            subprocess.Popen(cmd)
            self.status_label.set_label('Bootstrap launched')
            self.append_output('Launched bootstrap in terminal.')
        except Exception as exc:
            self.append_output(f'Launch failed: {exc}')
            self.status_label.set_label('Launch failed')

    def on_install_desktop(self, *_args):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        launcher = f'''[Desktop Entry]\nType=Application\nName=CachyOS Dev Bootstrap\nExec=python3 {shlex.quote(str(Path(__file__).resolve()))}\nIcon=applications-development\nTerminal=false\nCategories=Development;Utility;\n'''
        DESKTOP_PATH.parent.mkdir(parents=True, exist_ok=True)
        DESKTOP_PATH.write_text(launcher, encoding='utf-8')
        self.append_output(f'Desktop launcher installed: {DESKTOP_PATH}')
        self.status_label.set_label('Desktop launcher installed')

    def on_health_check(self, *_args):
        checks = [
            ('python3', 'python3 --version'),
            ('pacman', 'pacman --version | head -n 1'),
            ('paru', 'paru --version | head -n 1'),
            ('ollama', 'ollama --version'),
            ('code', 'code --version | head -n 1'),
            ('codium', 'codium --version | head -n 1'),
            ('docker', 'docker --version'),
            ('systemctl', 'systemctl is-active ollama || true'),
        ]
        out = []
        for name, cmd in checks:
            try:
                result = subprocess.run(['bash', '-lc', cmd], capture_output=True, text=True, timeout=8)
                text = (result.stdout or result.stderr).strip() or 'not found / no output'
                out.append(f'[{name}] {text}')
            except Exception as exc:
                out.append(f'[{name}] error: {exc}')
        out.append(f'AUR suggestions: {", ".join(AUR_HINTS)}')
        self.append_output('\n'.join(out))
        self.status_label.set_label('Health check complete')

    def load_config(self) -> AppConfig:
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
            return AppConfig(**data)
        except Exception:
            return AppConfig()


def shutil_which(name: str):
    return GLib.find_program_in_path(name)


class BootstrapApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.FLAGS_NONE)

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = BootstrapWindow(self)
        win.present()


if __name__ == '__main__':
    app = BootstrapApp()
    raise SystemExit(app.run())
