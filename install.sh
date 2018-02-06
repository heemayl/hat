#!/usr/bin/env bash

# Installer file for HAT (Hyper-AT)

(( EUID == 0 )) || { echo "Please run as superuser e.g. `sudo ./install.sh`" && \
			   exit 1 ;}

export PATH='/bin:/usr/bin:/sbin:/usr/sbin'

HAT_DIR='/usr/lib/hatd'
mkdir -p "${HAT_DIR}"

# Copy everything to `$HAT_DIR`
GLOBIGNORE='install.sh'
cp -aRt "${HAT_DIR}" *

# Put Systemd file for the daemon in relevant place
cp "${HAT_DIR}"/system/hat-daemon.service /etc/systemd/system/

# Create symlink for the client
ln -sf "${HAT_DIR}"/hat-client /usr/bin/hatc

# Create log dir
mkdir -p /var/log/hatd/

# Start the daemon
systemctl daemon-reload
systemctl start hatd.service

# Print done msg
echo 'Installation Done and daemon started! Now, please check `hatc --help`'

