# Maintainer: Mystical Mahnke <mysticalmahnke16@gmail.com>
pkgname=cachyos-dev-bootstrap
pkgver=1.0.0
pkgrel=1
pkgdesc="GTK4 bootstrap app for CachyOS / Arch-based Linux development setup"
arch=('any')
url="https://github.com/mmahnke16/cachyos-bootstrap-gui-repo"
license=('MIT')
depends=('python' 'gtk4' 'python-gobject' 'libadwaita' 'zenity')
makedepends=('git')
source=("git+$url.git")
sha256sums=('SKIP')

package() {
	cd "$srcdir/cachyos-bootstrap-gui-repo"
	
	install -Dm755 bootstrap_gui.py "$pkgdir/usr/bin/cachyos-dev-bootstrap"
	install -Dm644 LICENSE "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
	install -Dm644 README.md "$pkgdir/usr/share/doc/$pkgname/README.md"
    
    # Create desktop entry
    mkdir -p "$pkgdir/usr/share/applications"
    cat > "$pkgdir/usr/share/applications/cachyos-dev-bootstrap.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=CachyOS Dev Bootstrap
Exec=cachyos-dev-bootstrap
Icon=utilities-terminal
Terminal=false
Categories=Development;Utility;
EOF
}
