#!/bin/bash

# github.com/douxxtech | git.douxx.tech/piwave

# ========== FUNCTIONS ==========

print_magenta() {
  echo -e "\e[35m$1\e[0m"
}

check_status() {
  if [ $? -ne 0 ]; then
    echo -e "\e[31mError: $1 failed\e[0m"
    exit 1
  fi
}

show_warning_fmt() {
  if [ "$NO_WAIT" = true ]; then
    echo -e "\e[33mSkipping warning countdown (--no-wait provided)\e[0m"
    return
  fi

  echo -e "\e[33m"
  echo "==========================================================="
  echo " WARNING: You chose to install fm_transmitter (--install_fmt)."
  echo " On newer Raspberry Pi operating systems, building fm_transmitter can"
  echo " potentially BREAK some system components."
  echo ""
  echo " If you're unsure, press CTRL+C now to cancel!"
  echo " Continuing in 10 seconds..."
  echo "==========================================================="
  echo -e "\e[0m"

  for i in {10..1}; do
    echo -ne "Proceeding in $i seconds...\r"
    sleep 1
  done
  echo ""
}

# ========== ARG PARSING ==========
INSTALL_FMT=false
NO_WAIT=false
for arg in "$@"; do
  case $arg in
    --install_fmt)
      INSTALL_FMT=true
      shift
      ;;
    --no-wait)
      NO_WAIT=true
      shift
      ;;
    *)
      ;;
  esac
done

# ========== BANNER ==========
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

# ========== MAIN SETUP ==========
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

# ---------- PiFmRds ----------
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

if [[ $(tr -d '\0' < /proc/device-tree/model) == *"Zero 2 W"* ]]; then
    echo "Detected Raspberry Pi Zero 2 W. Patching Makefile..."
    if [ -f Makefile ]; then
        echo "Patching Makefile for Zero 2 W (RPI_VERSION=3)"
        sed -i 's/^RPI_VERSION :=.*/RPI_VERSION = 3/' Makefile
    else
        echo "Makefile not found in src! Cannot patch."
        exit 1
    fi
    check_status "Patching Makefile"
fi

sudo make
check_status "Building PiFmRds"

echo "Returning to installation directory..."
cd "$INSTALL_DIR" || { echo -e "\e[31mError: cd back to $INSTALL_DIR failed\e[0m"; exit 1; }

# ---------- fm_transmitter if we want it ----------
if [ "$INSTALL_FMT" = true ]; then
  show_warning_fmt

  echo "Installing additional dependencies for fm_transmitter..."
  sudo apt install -y libraspberrypi-dev
  check_status "Installing libraspberrypi-dev"

  echo "Cloning fm_transmitter into $INSTALL_DIR..."
  if [ ! -d "$INSTALL_DIR/fm_transmitter" ]; then
    sudo git clone https://github.com/markondej/fm_transmitter "$INSTALL_DIR/fm_transmitter"
    check_status "Cloning fm_transmitter"
  else
    echo "fm_transmitter already cloned, skipping..."
  fi

  echo "Building fm_transmitter..."
  cd "$INSTALL_DIR/fm_transmitter" || { echo -e "\e[31mError: cd to fm_transmitter failed\e[0m"; exit 1; }
  sudo make
  check_status "Building fm_transmitter"

  cd "$INSTALL_DIR" || { echo -e "\e[31mError: cd back to $INSTALL_DIR failed\e[0m"; exit 1; }
fi

# ========== FINISH ==========
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
if [ "$INSTALL_FMT" = true ]; then
  echo ""
  echo "fm_transmitter has been installed in: $INSTALL_DIR/fm_transmitter"
fi
echo "==========================================================="
