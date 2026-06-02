#!/usr/bin/env bash

JSON_SERVICE_REPO_URL="https://github.com/microsoft/vscode-json-languageservice"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SERVER_DIR="${SCRIPT_DIR}"
VSCODE_JSON_LANGUAGESERVICE_NAME="vscode-json-languageservice"
CLONED_JSON_SERVICE_DIR="${SERVER_DIR}/${VSCODE_JSON_LANGUAGESERVICE_NAME}"
PATCHES_DIR="${SERVER_DIR}/source-patches"

json_service_version="$1"

if [ -z "${json_service_version}" ]; then
    echo "Usage: $0 <json_service_version>"
    exit 1
fi

# -------- #
# clean up #
# -------- #

pushd "${SERVER_DIR}" > /dev/null || exit

echo "Removing ${CLONED_JSON_SERVICE_DIR}"
rm -rf "${CLONED_JSON_SERVICE_DIR}"

popd > /dev/null || exit

# ------------------ #
# clone json service #
# ------------------ #

pushd "${SERVER_DIR}" > /dev/null  || exit

echo "Cloning ${JSON_SERVICE_REPO_URL}"
git clone ${JSON_SERVICE_REPO_URL} --branch "v${json_service_version}" --single-branch "${VSCODE_JSON_LANGUAGESERVICE_NAME}"

popd > /dev/null  || exit

# -------------------- #
# prepare json service #
# -------------------- #

pushd "${CLONED_JSON_SERVICE_DIR}" > /dev/null  || exit

echo 'Applying patches...'
for patch in "${PATCHES_DIR}"/*.patch; do
    if ! git apply "${patch}"; then
        patch_subject=$(grep '^Subject: ' "${patch}" | sed 's/^Subject: \[PATCH[^]]*\] //')
        echo "Patch ${patch} failed to apply cleanly. You can try applying it with 3-way merge by running:"
        echo "  cd \"${CLONED_JSON_SERVICE_DIR}\" && git apply --3way \"${patch}\""
        echo "After resolving conflicts, recreate the patch by running:"
        echo "  cd \"${CLONED_JSON_SERVICE_DIR}\" && git add -A && git commit -m '${patch_subject}' && git format-patch HEAD~1 --output \"${patch}\""
        exit 1
    fi
done

npm i || exit
npm run prepack || exit

# Create a tarball of the package with .npmignore applied and then unpack so that we don't have any extra files.
echo "Creating package file for ${VSCODE_JSON_LANGUAGESERVICE_NAME}..."
pack_output=$(npm --silent --foreground-scripts=false pack --json --no-color --pack-destination "${SERVER_DIR}" || exit)
archive_name=$(echo "$pack_output" | jq '.[0].filename' --raw-output) || exit

popd > /dev/null  || exit

# ------------------ #
# Setup dependencies #
# ------------------ #

pushd "${SERVER_DIR}" > /dev/null || exit

rm -rf "${CLONED_JSON_SERVICE_DIR}"

npm i || exit

popd > /dev/null || exit

# -------------------------------- #
# override json service dependency #
# -------------------------------- #

pushd "${SERVER_DIR}" > /dev/null || exit

echo "Created archive ${archive_name}"
echo "Extracting archive ${archive_name} to 'package'..."
tar -xzf "${archive_name}" || exit
rm ${archive_name} || exit

echo "Overwriting compiled files in ${VSCODE_JSON_LANGUAGESERVICE_NAME}..."
rm -rf "${SERVER_DIR}/node_modules/${VSCODE_JSON_LANGUAGESERVICE_NAME}" || exit
mv package "${SERVER_DIR}/node_modules/${VSCODE_JSON_LANGUAGESERVICE_NAME}" || exit

popd > /dev/null  || exit

# ------------------------------------------ #
# Create patches for overridden json service #
# ------------------------------------------ #

pushd "${SERVER_DIR}" > /dev/null || exit

echo 'Setting up patch-package dependency...'
npm i patch-package || exit
jq ".scripts[\"postinstall\"] = \"patch-package\"" package.json > temp.json || exit
mv temp.json package.json || exit

echo "Patching ${VSCODE_JSON_LANGUAGESERVICE_NAME}..."
npx patch-package --error-on-fail "${VSCODE_JSON_LANGUAGESERVICE_NAME}" || exit

npm i || exit

popd > /dev/null || exit

# -------- #
# Clean up #
# -------- #

pushd "${SERVER_DIR}" > /dev/null || exit

rm -rf node_modules

popd > /dev/null || exit
