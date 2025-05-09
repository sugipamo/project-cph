if [ $# -eq 0 ]; then
  PYTHONPATH=src pytest --cov=src tests
else
  PYTHONPATH=src pytest "$@"
fi