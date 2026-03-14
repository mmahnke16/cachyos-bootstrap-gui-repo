import sys
from unittest.mock import MagicMock

# Mock gi module before importing bootstrap_gui
sys.modules['gi'] = MagicMock()
sys.modules['gi.repository'] = MagicMock()
sys.modules['gi.repository.Gtk'] = MagicMock()
sys.modules['gi.repository.Gio'] = MagicMock()
sys.modules['gi.repository.GLib'] = MagicMock()

from bootstrap_gui import AppConfig, generate_bootstrap_script, PKG_GROUPS

def test_app_config_defaults():
    cfg = AppConfig()
    assert cfg.editor == 'code'
    assert cfg.model == 'qwen2.5-coder:7b'
    assert cfg.install_ollama is True
    assert cfg.groups is not None
    # Check default groups are active
    assert cfg.groups.get('base') is True
    assert cfg.groups.get('python') is True

def test_generate_script_defaults():
    cfg = AppConfig()
    script = generate_bootstrap_script(cfg)
    
    assert "#!/usr/bin/env bash" in script
    assert "sudo pacman -Syu" in script
    assert "git" in script  # from base group
    assert "python-pip" in script  # from python group
    assert "code" in script  # default editor
    assert "ollama pull" in script
    assert "qwen2.5-coder:7b" in script

def test_generate_script_custom():
    cfg = AppConfig(
        editor='skip',
        model='skip',
        install_ollama=False,
        groups={'base': True, 'python': False},
        extra_pacman='firefox vlc',
        extra_aur='google-chrome',
        extra_commands='echo "Hello World"'
    )
    script = generate_bootstrap_script(cfg)
    
    assert "git" in script
    assert "python-pip" not in script
    # code might be in the helper function, but should not be in the install list
    # The install list looks like: sudo pacman -S ... pkg1 pkg2 ...
    # We can check that "code" is not in the pacman command line.
    # Simple check: it shouldn't be in the list of args passed to pacman
    # But for simplicity in this regex-less check:
    assert "pacman -S --needed --noconfirm code" not in script 
    assert "ollama pull" not in script
    assert "Skipping Ollama install" in script
    assert "firefox" in script
    assert "vlc" in script
    assert "google-chrome" in script
    assert 'echo "Hello World"' in script
    assert "paru -S" in script  # for AUR packages

def test_pkg_groups_integrity():
    # Ensure all groups in PKG_GROUPS are strings
    for group, pkgs in PKG_GROUPS.items():
        assert isinstance(pkgs, list)
        for pkg in pkgs:
            assert isinstance(pkg, str)
