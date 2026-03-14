#!/usr/bin/env bash
set -euo pipefail
sudo pacman -Syu --noconfirm
sudo pacman -S --needed --noconfirm python python-gobject gtk4 zenity
