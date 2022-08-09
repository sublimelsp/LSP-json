#!/usr/bin/env bash

GITHUB_REPO_URL="https://github.com/microsoft/vscode"
GITHUB_REPO_NAME=$(echo "${GITHUB_REPO_URL}" | command grep -oE '[^/]*$')

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_DIR="${SCRIPT_DIR}"
CLONED_REPO_DIR="${REPO_DIR}/temp"
SRC_SERVER_DIR="${CLONED_REPO_DIR}/extensions/json-language-features/server/"

echo "Your node version: $(node --version || echo '<missing>')"
echo "Your yarn version: $(yarn --version || echo '<missing>')"
read -rp "You need at least version 16 of Node and yarn installed (npm i -g yarn). Exit the script if it doesn't match requirements. Otherwise press enter."

# -------- #
# clean up #
# -------- #

pushd "${REPO_DIR}" || exit

rm -rf out package-lock.json package.json update-info.log

popd || exit


# ---------------- #
# clone repo       #
# ---------------- #

pushd "${REPO_DIR}" || exit

echo 'Enter commit SHA, branch or tag (for example 2.1.0) to build'
read -rp 'SHA, branch or tag (default: main): ' ref

if [ "${ref}" = "" ]; then
    ref="main"
fi

echo "Cloning ${GITHUB_REPO_URL}"
git clone ${GITHUB_REPO_URL} --branch ${ref} --single-branch "${CLONED_REPO_DIR}" || echo "Repo already cloned. Continuing..."
current_sha=$( git rev-parse HEAD )
printf "ref: %s\n%s\n" "$ref" "$current_sha" > update-info.log

popd || exit

# ------------ #
# prepare deps #
# ------------ #

pushd "${CLONED_REPO_DIR}" || exit

echo 'Installing dependencies...'
yarn

popd || exit

# ------- #
# compile #
# ------- #

pushd "${SRC_SERVER_DIR}" || exit

echo 'Compiling server...'
yarn compile

popd || exit

# -------------------- #
# collect output files #
# -------------------- #

pushd "${SRC_SERVER_DIR}" || exit

echo 'Copying and cleaning up files...'
find ./out -name "*.map" -delete
cp -r bin out package.json README.md "${REPO_DIR}"
rm -rf "${CLONED_REPO_DIR}"

# ---------------- #
# Update lock file #
# ---------------- #

pushd "${REPO_DIR}" || exit

echo 'Updating the lock file...'
npm i --production
rm -rf node_modules

popd || exit
