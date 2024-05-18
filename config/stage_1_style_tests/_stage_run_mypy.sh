#!/bin/bash
source config/common.sh

set -x

echo -e '\n'
echo 'Running mypy check...'

configure_script

FAILED=0
LABS=$(get_labs)

mypy config seminars admin_utils

check_if_failed

if [ -d "core_utils" ]; then
  echo "core_utils exist"
  mypy core_utils

  check_if_failed
fi

for LAB_NAME in $LABS; do
  echo "Running mypy for lab ${LAB_NAME}"
  TARGET_SCORE=$(get_score ${LAB_NAME})

  if [[ ${TARGET_SCORE} -gt 7 ]]; then
    echo "Running mypy checks for marks 8 and 10"
    mypy ${LAB_NAME}
  else
    continue
  fi
  check_if_failed

done

echo "Mypy check passed."
