#!/bin/bash

if [ $# -eq 0 ]; then
  pytest --cov=src
else
  pytest --cov=src "$@"
fi