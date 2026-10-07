#!/usr/bin/env bash
# ==============================================================================
# Host Prerequisites & Environment Bootstrap
# Huawei Cloud IMS Image Factory
# ==============================================================================

set -euo pipefail

WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN_DIR="${WORKSPACE_DIR}/bin"
VENV_DIR="${WORKSPACE_DIR}/.venv"

mkdir -p "${BIN_DIR}"

echo "======================================================================"
echo " [Huawei Cloud IMS] Verifying & Bootstrapping Prerequisites"
echo " Workspace: ${WORKSPACE_DIR}"
echo "======================================================================"

# Terminal color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

check_cmd() {
    if command -v "$1" &> /dev/null; then
        echo -e " [${GREEN}OK${NC}] Found: $1 ($(command -v "$1"))"
        return 0
    else
        echo -e " [${YELLOW}MISSING${NC}] Not found: $1"
        return 1
    fi
}

echo -e "\n${BLUE}1. Checking system packages...${NC}"
MISSING_PKGS=()

command -v qemu-img &> /dev/null || [ -x "${BIN_DIR}/qemu-img" ] || MISSING_PKGS+=("qemu-utils")
command -v qemu-system-x86_64 &> /dev/null || MISSING_PKGS+=("qemu-system-x86")
command -v fdisk &> /dev/null || MISSING_PKGS+=("fdisk")
command -v parted &> /dev/null || MISSING_PKGS+=("parted")
command -v curl &> /dev/null || MISSING_PKGS+=("curl")
command -v wget &> /dev/null || MISSING_PKGS+=("wget")
command -v tar &> /dev/null || MISSING_PKGS+=("tar")
command -v python3 &> /dev/null || MISSING_PKGS+=("python3")
command -v pip3 &> /dev/null || MISSING_PKGS+=("python3-pip")

if [ ${#MISSING_PKGS[@]} -eq 0 ]; then
    echo -e "${GREEN}All required system packages are present.${NC}"
else
    echo -e "${YELLOW}Pending packages:${NC} ${MISSING_PKGS[*]}"
    if [ "$EUID" -ne 0 ]; then
        if sudo -n true 2>/dev/null; then
            echo -e "${BLUE}Installing packages via sudo apt...${NC}"
            sudo apt-get update -y
            sudo apt-get install -y "${MISSING_PKGS[@]}"
        else
            echo -e "${YELLOW}Note: Sudo privileges required to install host packages.${NC}"
            echo -e "Run manually in your terminal:"
            echo -e "  ${GREEN}sudo apt-get update && sudo apt-get install -y ${MISSING_PKGS[*]}${NC}\n"
        fi
    else
        apt-get update -y
        apt-get install -y "${MISSING_PKGS[@]}"
    fi
fi

# 2. Python Virtual Environment Setup
echo -e "\n${BLUE}2. Configuring Python virtualenv...${NC}"
if [ ! -d "${VENV_DIR}" ]; then
    echo "Creating virtualenv at ${VENV_DIR}..."
    python3 -m venv "${VENV_DIR}"
fi

echo "Installing Python dependencies..."
"${VENV_DIR}/bin/pip" install --upgrade pip > /dev/null 2>&1 || true
if [ -f "${WORKSPACE_DIR}/requirements.txt" ]; then
    "${VENV_DIR}/bin/pip" install -r "${WORKSPACE_DIR}/requirements.txt"
fi
echo -e " [${GREEN}OK${NC}] Python environment ready."

# 3. Huawei obsutil verification
echo -e "\n${BLUE}3. Checking Huawei obsutil CLI...${NC}"
OBSUTIL_PATH="${BIN_DIR}/obsutil"
if [ -f "${OBSUTIL_PATH}" ] && [ -x "${OBSUTIL_PATH}" ]; then
    echo -e " [${GREEN}OK${NC}] obsutil ready at: ${OBSUTIL_PATH}"
else
    echo "Downloading official Huawei obsutil binary to ${BIN_DIR}..."
    TMP_OBS_TAR="/tmp/obsutil_linux_amd64.tar.gz"
    DOWNLOAD_SUCCESS=0
    for URL in \
        "https://obs-community.obs.eu-west-101.myhuaweicloud.eu/obsutil/current/obsutil_linux_amd64.tar.gz" \
        "https://obs-community.obs.ap-southeast-1.myhuaweicloud.com/obsutil/current/obsutil_linux_amd64.tar.gz" \
        "https://obs-community.obs.cn-north-1.myhuaweicloud.com/obsutil/current/obsutil_linux_amd64.tar.gz"
    do
        echo "Trying: ${URL}..."
        if curl -fsSL -m 15 "${URL}" -o "${TMP_OBS_TAR}" 2>/dev/null; then
            DOWNLOAD_SUCCESS=1
            break
        fi
    done

    if [ ${DOWNLOAD_SUCCESS} -eq 1 ] && [ -f "${TMP_OBS_TAR}" ]; then
        TMP_DIR="/tmp/obsutil_extract_$$"
        mkdir -p "${TMP_DIR}"
        tar -xzf "${TMP_OBS_TAR}" -C "${TMP_DIR}"
        EXTRACTED_BIN=$(find "${TMP_DIR}" -type f -name "obsutil" | head -n 1)
        if [ -n "${EXTRACTED_BIN}" ]; then
            cp -f "${EXTRACTED_BIN}" "${OBSUTIL_PATH}"
            chmod +x "${OBSUTIL_PATH}"
            echo -e " [${GREEN}OK${NC}] obsutil installed to: ${OBSUTIL_PATH}"
        fi
        rm -rf "${TMP_DIR}" "${TMP_OBS_TAR}"
    else
        echo -e " [${YELLOW}INFO${NC}] Could not download obsutil automatically. Direct Python SDK/API fallback is active."
    fi
fi

# 4. Workspace directory layout
echo -e "\n${BLUE}4. Ensuring workspace directories...${NC}"
for DIR in downloads extracao_imagem imagem scripts documentacao wiki_guide; do
    mkdir -p "${WORKSPACE_DIR}/${DIR}"
    echo -e " [${GREEN}OK${NC}] Directory ready: ${DIR}/"
done

export PATH="${BIN_DIR}:${PATH}"

echo -e "\n======================================================================"
echo -e " ${GREEN}Prerequisites check completed.${NC}"
echo -e " To activate the Python virtualenv:"
echo -e "   source .venv/bin/activate"
echo -e "======================================================================"
