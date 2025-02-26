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


echo "Creating the PiWave_deps directory..."
mkdir -p PiWave_deps
check_status "Creating directory PiWave_deps"

echo "Changing to the PiWave_deps directory..."
cd PiWave_deps || { echo -e "\e[31mError: cd to PiWave_deps failed\e[0m"; exit 1; }

echo "Updating package lists..."
sudo apt update
check_status "Updating package lists"

echo "Installing required packages..."
sudo apt install -y python3 libsndfile1-dev make ffmpeg git
check_status "Installing required packages"

echo "Installing PiWave..."
sudo pip install git+https://github.com/douxxtech/piwave.git --break-system-packages
check_status "Installing PiWave"

echo "Cloning PiFmRds..."
sudo git clone https://github.com/ChristopheJacquet/PiFmRds
check_status "Cloning PiFmRds"

echo "Changing to PiFmRds/src directory..."
cd PiFmRds/src || { echo -e "\e[31mError: cd to PiFmRds/src failed\e[0m"; exit 1; }

echo "Cleaning previous builds..."
sudo make clean
check_status "Cleaning previous builds"

echo "Building PiFmRds..."
sudo make
check_status "Building PiFmRds"

echo "Returning to the previous directory..."
cd ../../../ || { echo -e "\e[31mError: cd back to previous directory failed\e[0m"; exit 1; }

echo "Setup completed successfully!"
