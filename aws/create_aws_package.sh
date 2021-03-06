#!/bin/bash
set -e
project_root="$(dirname "${BASH_SOURCE[0]}")"

pushd "${project_root}" >/dev/null

rm -rf python aws_package.zip

packages=($(find . -maxdepth 1 -type f -name '*.py' -exec grep -h import -- {} + | \
    awk '/from/{print $2} !/from/{print $NF}' | sort -u | \
    grep -v -e AllegroScraper -e boto3 -e hashlib -e json -e random -e time -e urllib))

pip install "${packages[@]}" -t ./python
cp -t ./python AllegroScraper.py

zip -r aws_package python

popd >/dev/null
