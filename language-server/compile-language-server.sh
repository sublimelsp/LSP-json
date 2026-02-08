#!/usr/bin/env bash

VSCODE_REPO_URL="https://github.com/microsoft/vscode"
JSON_SERVICE_REPO_URL="https://github.com/microsoft/vscode-json-languageservice"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_DIR="${SCRIPT_DIR}"
CLONED_VSCODE_DIR="${REPO_DIR}/temp"
SRC_SERVER_DIR="${CLONED_VSCODE_DIR}/extensions/json-language-features/server/"
CLONED_JSON_SERVICE_DIR="${REPO_DIR}/temp2"

echo "Your node version: $(node --version || echo '<missing>')"
read -rp "You need at least version 22 of Node. Exit the script if it doesn't match requirements. Otherwise press enter."

# -------- #
# clean up #
# -------- #

pushd "${REPO_DIR}" || exit

rm -rf out package-lock.json package.json update-info.log *.tgz "${CLONED_VSCODE_DIR}" "${CLONED_JSON_SERVICE_DIR}"

popd || exit

# ------------ #
# clone vscode #
# ------------ #

pushd "${REPO_DIR}" || exit

echo 'Enter commit SHA, branch or tag (for example 2.1.0) to build'
read -rp 'SHA, branch or tag (default: main): ' ref

if [ "${ref}" = "" ]; then
    ref="main"
fi

echo "Cloning ${VSCODE_REPO_URL}"
git clone ${VSCODE_REPO_URL} --branch ${ref} --single-branch "${CLONED_VSCODE_DIR}" || echo "Repo already cloned. Continuing..."
current_sha=$( git rev-parse HEAD )
printf "ref: %s\n%s\n" "$ref" "$current_sha" > update-info.log

popd || exit

# ------------ #
# prepare deps #
# ------------ #

pushd "${CLONED_VSCODE_DIR}" || exit

echo 'Installing dependencies...'
npm i

popd || exit

# ------- #
# compile #
# ------- #

pushd "${SRC_SERVER_DIR}" || exit

# Get exact version of vscode-json-languageservice
json_service_version=$(npm ls --json --depth=0 vscode-json-languageservice | jq '.dependencies["vscode-json-languageservice"].version' --raw-output) || exit

echo 'Compiling server...'
npm run compile

popd || exit

# -------------------- #
# collect output files #
# -------------------- #

pushd "${SRC_SERVER_DIR}" || exit

echo 'Copying and cleaning up files...'
find ./out -name "*.map" -delete
cp -r out package.json README.md "${REPO_DIR}"
rm -rf "${CLONED_VSCODE_DIR}"

popd || exit

# ------------------ #
# clone json service #
# ------------------ #

pushd "${REPO_DIR}" || exit

echo "Cloning ${JSON_SERVICE_REPO_URL}"
git clone ${JSON_SERVICE_REPO_URL} --branch "v${json_service_version}" --single-branch "${CLONED_JSON_SERVICE_DIR}" || echo "Repo already cloned. Continuing..."

popd || exit

# -------------------- #
# prepare json service #
# -------------------- #

pushd "${CLONED_JSON_SERVICE_DIR}" || exit

# Add support for sublime colors (implementation in https://github.com/rchl/vscode-json-languageservice/tree/feat/st-colors)
git apply "${REPO_DIR}/0001-feat-support-sublime-text-colors.patch" || exit

echo 'Installing dependencies...'
npm i || exit
pack_output=$(npm --silent --foreground-scripts=false pack --json --no-color --pack-destination "${REPO_DIR}" || exit)
archive_name=$(echo "$pack_output" | jq '.[0].filename' --raw-output) || exit

popd || exit

# -------------------------------- #
# override json service dependency #
# -------------------------------- #

pushd "${REPO_DIR}" || exit

rm -rf "${CLONED_JSON_SERVICE_DIR}"

# Override vscode-json-languageservice dependency with local one
jq ".dependencies[\"vscode-json-languageservice\"] = \"file:${archive_name}\"" package.json > temp.json || exit
mv temp.json package.json || exit

popd || exit

# ---------------- #
# Update lock file #
# ---------------- #

pushd "${REPO_DIR}" || exit

echo 'Updating the lock file...'
npm i --omit=dev --lockfile-version=2
rm -rf node_modules

popd || exit
