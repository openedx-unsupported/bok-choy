#!/usr/bin/env bash

 if [ ! -f /usr/local/bin/browsermob-proxy ]; then
    if [ ! -d /etc/browsermob-proxy ]; then
        # get the package and put it in /etc/browsermob-proxy
        echo "Fetching browsermob-proxy package."
        curl 'https://s3-us-west-1.amazonaws.com/lightbody-bmp/browsermob-proxy-2.0-beta-9-bin.zip' > /var/tmp/bmp.zip
        cd /var/tmp
        unzip /var/tmp/bmp.zip
        mv /var/tmp/browsermob-proxy-2.0-beta-9 /etc/browsermob-proxy
    else
        echo "browsermob-proxy package found."
    fi

    echo "Finishing installation of browsermob-proxy."
    # make sure the packages main script is executable
    chmod 0755 /etc/browsermob-proxy/bin/browsermob-proxy

    # route /usr/local/bin/browsermob-proxy to the actual package
    cat > /usr/local/bin/browsermob-proxy << EOF
#!/bin/sh
/etc/browsermob-proxy/bin/browsermob-proxy
EOF
else
    echo "browsermob-proxy already installed."
fi

# Make sure it is executable
chmod 0755 /usr/local/bin/browsermob-proxy
echo "Done."
