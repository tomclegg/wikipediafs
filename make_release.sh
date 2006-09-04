#!/bin/sh

RM="`which rm` -vrf"
MKDIR="`which mkdir` -p"

if [ "$1foo" = "foo" ]; then
        echo "usage: `basename $0` X.Y.Z"
        exit 1
fi

PKG="wikipediafs-$1"
TAR_PKG="$PKG.tar.gz"
ZIP_PKG="$PKG.zip"
TMP_DIR="/tmp/$PKG"

echo "Creating temporary directory..."
$RM $TMP_DIR
$MKDIR $TMP_DIR
cp -r * $TMP_DIR
cd $TMP_DIR

echo "Creating man page"
docbook-to-man doc/mount.wikipediafs.sgml > doc/mount.wikipediafs.1
man2html -r doc/mount.wikipediafs.1 | sed -e "s/Content-type: text\/html//" \
    > doc/mount.wikipediafs.htm
gzip doc/mount.wikipediafs.1

echo "Uploading site..."
cp README README.txt
scp site/*.htm doc/mount.wikipediafs.htm README.txt \
mblondel@shell.sourceforge.net:/home/groups/w/wi/wikipediafs/htdocs/
$RM README.txt

echo "Removing unnecessary files..."
$RM `find . -name "*.pyc" -or -name ".*" -or -name "*~" -or -name "*.orig"`
$RM "make_release.sh"

echo "Updating version number..."
echo "VERSION = '"$1"'" > src/wikipediafs/version.py
echo $1 > VERSION

cd ..

echo "Generating tarball..."
$RM $TAR_PKG 
tar -czf $TAR_PKG $PKG

echo "Generating zip..."
$RM $ZIP_PKG 
zip -r $ZIP_PKG $PKG

echo "Generated archives:"
du -h "`dirname $TMP_DIR`/$TAR_PKG"
du -h "`dirname $TMP_DIR`/$ZIP_PKG"

exit 0
