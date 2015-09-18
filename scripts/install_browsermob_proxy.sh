#!/usr/bin/env bash
BMP_VERSION="2.1.0-beta-3"
BMP_NAME="browsermob-proxy-$BMP_VERSION"
BMP_URL="https://github.com/lightbody/browsermob-proxy/releases/download/$BMP_NAME/$BMP_NAME-bin.zip"

 if [ ! -f /usr/local/bin/browsermob-proxy ]; then
    if [ ! -d /etc/browsermob-proxy ]; then
        # get the package and put it in /etc/browsermob-proxy
        echo "Fetching browsermob-proxy package."
        # Use "-L" to follow redirects, which github uses in order to
        # specify the access token for the AWS bucket where it keeps the file
        curl -L $BMP_URL > /var/tmp/bmp.zip
        cd /var/tmp
        unzip /var/tmp/bmp.zip
        mv /var/tmp/$BMP_NAME /etc/browsermob-proxy
    else
        echo "browsermob-proxy package found."
    fi

    echo "Finishing installation of browsermob-proxy."
    # make sure the packages main script is executable
    chmod 0755 /etc/browsermob-proxy/bin/browsermob-proxy

    # route /usr/local/bin/browsermob-proxy to the actual package
    cat > /usr/local/bin/browsermob-proxy << EOF
#!/bin/sh
/etc/browsermob-proxy/bin/browsermob-proxy \$*
EOF
else
    echo "browsermob-proxy already installed."
fi

# Make sure it is executable
chmod 0755 /usr/local/bin/browsermob-proxy
echo "Done."
