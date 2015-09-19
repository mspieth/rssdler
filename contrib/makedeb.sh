#!/bin/bash

# requires stdeb
# pip install stdeb

# run from base dir

DIR=tarball
VERSION=`python -c 'import rssdler; print "%s" % rssdler.__version__'`

echo "building $VERSION deb"

[ -d $DIR ] || mkdir $DIR
pushd $DIR

NAME=rssdler-$VERSION
TARBALL=$NAME.tar.gz

rm -rf $NAME
git clone .. $NAME
rm $TARBALL
tar czf $TARBALL $NAME

popd

py2dsc-deb $DIR/$TARBALL

