PKGTITLE="appleloops"
# PKGVERSION="3.0.0"
PKG_VERSION:=$(shell /usr/bin/awk -F '=' '/VERSION = / {print $$2}' src/loopslib/version.py | /usr/bin/sed -e "s/'//g" -e "s/ //g")
PKGVERSION="${PKG_VERSION}"
BUNDLEID="com.github.carlashley.appleloops"
PROJECT="appleloops"


pkg:
	rm -f dist/pkg/appleloops-*.pkg
	pkgbuild --root ./dist/zipapp --identifier ${BUNDLEID} --version ${PKGVERSION} --ownership recommended --preserve-xattr ./dist/pkg/${PKGTITLE}-${PKGVERSION}.component.pkg
	productbuild --identifier ${BUNDLEID} --package ./dist/pkg/${PKGTITLE}-${PKGVERSION}.component.pkg ./dist/pkg/appleloops-${PKGVERSION}.pkg
	rm -f dist/pkg/${PKGTITLE}-${PKGVERSION}.component.pkg
