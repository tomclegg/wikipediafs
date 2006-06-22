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

echo "Uploading site..."
scp site/*.htm \
mblondel@shell.sourceforge.net:/home/groups/w/wi/wikipediafs/htdocs/

echo "Creating temporary directory..."
$RM $TMP_DIR
$MKDIR $TMP_DIR
cp -r * $TMP_DIR
cd $TMP_DIR

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
