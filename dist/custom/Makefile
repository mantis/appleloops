PKGTITLE="appleloops"
PKG_VERSION:=$(shell /usr/bin/awk -F '=' '/VERSION = / {print $$2}' src/loopslib/version.py | /usr/bin/sed -e "s/'//g" -e "s/ //g")
PKGVERSION="${PKG_VERSION}"
BUNDLEID="com.github.carlashley.appleloops"
PROJECT="appleloops"


pkg:
	rm -f dist/custom/pkg/appleloops-*.pkg
	pkgbuild --root ./dist/custom/zipapp --identifier ${BUNDLEID} --version ${PKGVERSION} --ownership recommended --preserve-xattr ./dist/custom/pkg/${PKGTITLE}-${PKGVERSION}.component.pkg
	productbuild --identifier ${BUNDLEID} --package ./dist/custom/pkg/${PKGTITLE}-${PKGVERSION}.component.pkg ./dist/custom/pkg/appleloops-${PKGVERSION}.pkg
	rm -f dist/custom/pkg/${PKGTITLE}-${PKGVERSION}.component.pkg
