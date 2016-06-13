#!/usr/bin/env bash
BMP_VERSION="2.1.1"
BMP_NAME="browsermob-proxy-$BMP_VERSION"
BMP_URL="https://github.com/lightbody/browsermob-proxy/releases/download/$BMP_NAME/$BMP_NAME-bin.zip"
TEMP_BROWSERMOB_DIR="/var/tmp"
BROWSERMOB_INSTALL_LOC="/etc/browsermob-proxy"

if [ ! -z $TRAVIS ]; then
    TEMP_BROWSERMOB_DIR=browsermobtemp
    mkdir -p $TEMP_BROWSERMOB_DIR
    BROWSERMOB_INSTALL_LOC=$TEMP_BROWSERMOB_DIR/browsermob-proxy

fi

 if [ ! -f /usr/local/bin/browsermob-proxy ]; then
    if [ ! -d /etc/browsermob-proxy ]; then
        # get the package and put it in /etc/browsermob-proxy
        echo "Fetching browsermob-proxy package."
        # Use "-L" to follow redirects, which github uses in order to
        # specify the access token for the AWS bucket where it keeps the file
        curl -L $BMP_URL > $TEMP_BROWSERMOB_DIR/bmp.zip
        unzip $TEMP_BROWSERMOB_DIR/bmp.zip -d $TEMP_BROWSERMOB_DIR
        mv $TEMP_BROWSERMOB_DIR/$BMP_NAME $BROWSERMOB_INSTALL_LOC
    else
        echo "browsermob-proxy package found."
    fi

    echo "Finishing installation of browsermob-proxy."
    # make sure the packages main script is executable
    chmod 0755 $BROWSERMOB_INSTALL_LOC/bin


    if [ -z $TRAVIS ]; then
    # route /usr/local/bin/browsermob-proxy to the actual package
        cat > /usr/local/bin/browsermob-proxy << EOF
#!/bin/sh
/etc/browsermob-proxy/bin/browsermob-proxy \$*
EOF
    # Make sure it is executable
    chmod 0755 /usr/local/bin/browsermob-proxy
    fi
else
    echo "browsermob-proxy already installed."
fi

echo "Done."
