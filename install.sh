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

echo "Creating the PiWave installation directory at $INSTALL_DIR..."
sudo mkdir -p "$INSTALL_DIR"
check_status "Creating directory $INSTALL_DIR"

echo "Changing to the installation directory..."
cd "$INSTALL_DIR" || { echo -e "\e[31mError: cd to $INSTALL_DIR failed\e[0m"; exit 1; }

echo "Updating package lists..."
sudo apt update
check_status "Updating package lists"

echo "Installing required packages..."
sudo apt install -y python3 python3-pip libsndfile1-dev make ffmpeg git
check_status "Installing required packages"

echo "Cloning PiFmRds into $INSTALL_DIR..."
if [ ! -d "$INSTALL_DIR/PiFmRds" ]; then
  sudo git clone https://github.com/ChristopheJacquet/PiFmRds "$INSTALL_DIR/PiFmRds"
  check_status "Cloning PiFmRds"
else
  echo "PiFmRds already cloned, skipping..."
fi

echo "Building PiFmRds..."
cd "$INSTALL_DIR/PiFmRds/src" || { echo -e "\e[31mError: cd to PiFmRds/src failed\e[0m"; exit 1; }
sudo make clean
check_status "Cleaning previous builds"
sudo make
check_status "Building PiFmRds"

echo "Returning to installation directory..."
cd "$INSTALL_DIR" || { echo -e "\e[31mError: cd back to $INSTALL_DIR failed\e[0m"; exit 1; }

print_magenta "Setup completed successfully!"

echo ""
echo "==========================================================="
echo "Dependencies installed in: $INSTALL_DIR"
echo "=>  PiWave itself has NOT been installed automatically."
echo ""
echo "To install PiWave safely (without breaking system Python),"
echo "create a virtual environment and install it there:"
echo ""
echo "  python3 -m venv ~/piwave-env"
echo "  source ~/piwave-env/bin/activate"
echo "  pip install git+https://github.com/douxxtech/piwave.git"
echo ""
echo "After activation, you can run PiWave from the venv environment."
echo "==========================================================="
