#!/usr/bin/env bash

VSCODE_REPO_URL="https://github.com/microsoft/vscode"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SERVER_DIR="${SCRIPT_DIR}"
CLONED_VSCODE_DIR="${SERVER_DIR}/temp"
SRC_SERVER_DIR="${CLONED_VSCODE_DIR}/extensions/json-language-features/server/"

echo "Your node version: $(node --version || echo '<missing>')"
read -rp "You need at least version 22 of Node. Exit the script if it doesn't match requirements. Otherwise press enter."

# -------- #
# clean up #
# -------- #

pushd "${SERVER_DIR}" > /dev/null || exit

rm -rf out package-lock.json package.json update-info.log *.tgz "${CLONED_VSCODE_DIR}"

popd > /dev/null || exit

# ------------ #
# clone vscode #
# ------------ #

pushd "${SERVER_DIR}" > /dev/null || exit

echo "Fetching latest release tag from ${VSCODE_REPO_URL}..."
latest_tag=$(gh release view --repo microsoft/vscode --json tagName --jq '.tagName' 2>/dev/null)
default_ref="${latest_tag:-main}"

echo "Enter commit SHA, branch or tag (for example 2.1.0) from the ${VSCODE_REPO_URL} repo to build:"
read -rp "SHA, branch or tag (default: ${default_ref}): " ref

if [ "${ref}" = "" ]; then
    ref="${default_ref}"
fi

echo "Cloning ${VSCODE_REPO_URL}"
git clone ${VSCODE_REPO_URL} --branch ${ref} --single-branch "${CLONED_VSCODE_DIR}" || echo "Repo already cloned. Continuing..."
current_sha=$( git -C "${CLONED_VSCODE_DIR}" rev-parse HEAD )
printf "ref: %s\n%s\n" "$ref" "$current_sha" > update-info.log

popd > /dev/null || exit

# ------------ #
# prepare deps #
# ------------ #

pushd "${CLONED_VSCODE_DIR}" > /dev/null || exit

echo 'Installing dependencies...'
npm i

popd > /dev/null || exit

# ------- #
# compile #
# ------- #

pushd "${SRC_SERVER_DIR}" > /dev/null || exit

# Get exact version of vscode-json-languageservice
json_service_version=$(npm ls --json --depth=0 vscode-json-languageservice | jq '.dependencies["vscode-json-languageservice"].version' --raw-output) || exit

echo 'Compiling server...'
npm run compile

popd > /dev/null || exit

# -------------------- #
# collect output files #
# -------------------- #

pushd "${SRC_SERVER_DIR}" > /dev/null || exit

echo 'Copying and cleaning up files...'
find ./out -name "*.map" -delete
cp -r out package.json README.md "${SERVER_DIR}"
rm -rf "${CLONED_VSCODE_DIR}"

popd > /dev/null  || exit

"${SERVER_DIR}/override-json-languageservice.sh" "${json_service_version}"
