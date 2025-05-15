#!/bin/bash

if [ $# -eq 0 ]; then
  pytest --cov=src tests
else
  pytest "$@"
fi