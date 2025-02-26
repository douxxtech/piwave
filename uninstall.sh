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

echo "Stopping any running PiWave processes..."
sudo pkill -f piwave
check_status "Stopping PiWave processes"

echo "Uninstalling PiWave Python package..."
sudo pip uninstall -y piwave --break-system-packages
check_status "Uninstalling PiWave"

echo "Removing PiFmRds directory..."
sudo rm -rf PiFmRds
check_status "Removing PiFmRds directory"

echo "Removing PiWave_deps directory..."
cd .. || { echo -e "\e[31mError: cd to parent directory failed\e[0m"; exit 1; }
sudo rm -rf PiWave_deps
check_status "Removing PiWave_deps directory"

echo "Cleaning up residual configuration and dependencies..."
sudo apt autoremove -y
check_status "Cleaning residual files"

echo "Uninstallation completed successfully!"
