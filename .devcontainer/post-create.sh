#!/usr/bin/env bash

# Install dependencies
pip install --upgrade pip
pip install uv
uv pip install --system -r requirements.txt
