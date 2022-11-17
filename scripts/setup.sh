#!/usr/bin/env bash

# Stop on errors
set -e

echo "Preparing config folder..."
mkdir -p /config

FILE=".devcontainer/configuration.yaml"
[ -f $FILE ] && { echo "Linking configuration.yaml"; ln -sfr $FILE /config/configuration.yaml; }
FILE=".devcontainer/secrets.yaml"
[ -f $FILE ] && { echo "Linking secrets.yaml"; ln -sfr $FILE /config/secrets.yaml; }

echo "Linking custom_components"
rm -rf /config/custom_components
ln -sfr custom_components /config/custom_components
