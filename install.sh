#!/usr/bin/env bash

# Installer file for HAT (Hyper-AT)

(( EUID == 0 )) || { echo "Please run as superuser e.g. sudo ./install.sh" && \
			   exit 1 ;}

export PATH='/bin:/usr/bin:/sbin:/usr/sbin'

HAT_DIR='/usr/lib/hatd'
mkdir -p "${HAT_DIR}"

# Copy everything to `$HAT_DIR`
GLOBIGNORE='install.sh'
cp -aRt "${HAT_DIR}" *

# Put Systemd file for the daemon in relevant place.
# If this gives an error regarding wrong/absent destination directory,
# please put the file manually in your distro-advised place
cp "${HAT_DIR}"/system/hat-daemon.service /etc/systemd/system/

# Create symlink for the client
ln -sf "${HAT_DIR}"/hat-client /usr/bin/hatc

# Create log dir
mkdir -p /var/log/hatd/

# Copying the logrotate file
cp hat-daemon /etc/logrotate.d/

# Create `hatd` group and set SETGID on `/var/run/hatd/locks/`
addgroup hatd
mkdir -p /var/run/hatd/locks
chown :hatd /var/run/hatd/locks
chmod g+s /var/run/hatd/locks 

# Start the daemon
systemctl daemon-reload
systemctl enable hat-daemon.service
systemctl start hatd.service

# Print done msg
msgs=($'\nInstallation Done and daemon started!\n'
      'Now, do the following:'
      $'\t1. Add the user(s) who can schedule jobs to the `hatd` group e.g. for user `foobar`: usermod -a -G hatd foobar'
      $'\t2. Read `hatc --help`'
     )
      
printf '%s\n' "${msgs[@]}"
