#!/bin/bash
# github.com/douxxtech | git.douxx.tech/piwave 

print_magenta() {
  echo -e "\e[35m$1\e[0m"
}

check_status() {
  if [ $? -ne 0 ]; then
    echo -e "\e[31mError: $1 failed\e[0m"
    exit 1
  fi
}

print_magenta "
  ____  ___        __                   |                       !
 |  _ \(_) \      / /_ ___      _____    |                       |
 | |_) | |\ \ /\ / / _\` \ \ /\ / / _ \   |    |~/                |
 |  __/| | \ V  V / (_| |\ V  V /  __/   |   _|~                |
 |_|   |_|  \_/\_/ \__,_| \_/\_/ \___|   |  (_|   |~/            |
                                       |      _|~                |
                       .============.|  (_|   |~/              |
                     .-;____________;|.      _|~                |
                     | [_________I__] |     (_|                |
                     |  \"\"\"\"\"  (_) (_) |                            |
                     | .=====..=====. |                            |
                     | |:::::||:::::| |                            |
                     | '=====''=====' |                            |
                     '----------------'                            |
"

INSTALL_DIR="/opt/PiWave"

echo "Stopping any running PiWave processes..."
sudo pkill -f piwave 2>/dev/null
echo "PiWave processes stopped (if any)."

echo "Removing installation directory: $INSTALL_DIR ..."
if [ -d "$INSTALL_DIR" ]; then
  sudo rm -rf "$INSTALL_DIR"
  check_status "Removing $INSTALL_DIR"
else
  echo "Directory $INSTALL_DIR not found, skipping..."
fi

echo "Cleaning up residual packages..."
sudo apt autoremove -y
check_status "Cleaning residual packages"

print_magenta "Uninstallation completed successfully!"

echo ""
echo "==========================================================="
echo "All dependencies in $INSTALL_DIR have been removed."
echo "=> If you installed PiWave in a Python virtual environment,"
echo "   you should manually remove that environment, e.g.:"
echo ""
echo "   rm -rf ~/piwave-env"
echo ""
echo "==========================================================="
