set -ex

echo $1

DIRS_TO_CHECK=(
  "quality_control"
)

if [ -d "venv" ]; then
    echo "Taking Python from venv"
    source venv/bin/activate
    which python
else
    echo "Taking Python from global environment"
    which python
fi

export PYTHONPATH=$(pwd)

autoflake -vv .

python -m black "${DIRS_TO_CHECK[@]}"

isort "${DIRS_TO_CHECK[@]}"

python -m pylint "${DIRS_TO_CHECK[@]}"

# mypy "${DIRS_TO_CHECK[@]}"

python -m flake8 "${DIRS_TO_CHECK[@]}"

# python quality_control/static_checks/check_requirements.py
