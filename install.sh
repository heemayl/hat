#!/usr/bin/env bash

# Installer file for HAT (Hyper-AT)

(( EUID == 0 )) || { echo "Please run as superuser e.g. sudo ./install.sh" && \
			   exit 1 ;}

export PATH='/bin:/usr/bin:/sbin:/usr/sbin'

HAT_DIR='/usr/lib/hatd'
HAT_DB_DIR='/var/lib/hatd'
mkdir -p "${HAT_DIR}"

# Copy required stuffs to `$HAT_DIR`
cp -aRt "${HAT_DIR}" ./{hat{,d,-client},env_base.sh}

# Put Systemd file for the daemon in relevant place.
# If this gives an error regarding wrong/absent destination directory,
# please put the file manually in your distro-advised place
cp system/hat-daemon.service /etc/systemd/system/

# Create symlink for the client
ln -sf "${HAT_DIR}"/hat-client /usr/bin/hatc

# Create log dir
mkdir -p /var/log/hatd/

# Create DB file
[[ -f ${HAT_DB_DIR}/hatdb.pkl ]] || { mkdir -p "${HAT_DB_DIR}" && : >"${HAT_DB_DIR}"/hatdb.pkl ;}

# Copying the logrotate file
cp system/hat-daemon /etc/logrotate.d/

# Copying and gzip-ing man page
gzip --to-stdout system/hatc.1 >/usr/share/man/man1/hatc.1.gz

# Create `hatd` group and set SETGID on `/var/run/hatd/locks/`
addgroup hatd
mkdir -p /var/run/hatd/locks
chown :hatd /var/run/hatd/locks
chmod g+s /var/run/hatd/locks 

# Print done msg
msgs=($'\nInstallation Done and daemon started!\n'
      'Now, do the following:'
      $'\t1. Add the user(s) who can schedule jobs to the `hatd` group e.g. for user `foobar`: usermod -a -G hatd foobar'
      $'\t2. For group changes to take effect on any live session of the user, the user needs to logout of that session, and then login Or simply start a new session'
      $'\t3. Read `hatc --help`'
     )

# Start the daemon
systemctl daemon-reload
systemctl enable hat-daemon.service && \
    systemctl start hatd.service && { printf '%s\n' "${msgs[@]}" || printf '%s\n' "Installation Failed!" ;}


#
# To uninstall (as superuser):
#
# 1. Stop the dameon and remove init file:
#        systemctl stop hatd.service && \
#        rm /etc/systemd/system/hat-daemon.service && \
#        systemctl daemon-reload
# 2. Remove other files and directories:
#        rm -r /var/lib/hatd/ /var/run/hatd/ /usr/lib/hatd/ /etc/logrotate.d/hat-daemon /usr/share/man/man1/hatc.1.gz
#
# N.B: If you want to keep the enqueued jobs, don't remove `/var/lib/hatd/`, precisely `/var/lib/hatd/hatdb.pkl`.
#
