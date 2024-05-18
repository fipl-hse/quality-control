#!/bin/bash
source config/common.sh

set -x

echo -e '\n'
echo 'Running stubgen check...'

configure_script

FAILED=0
LABS=$(cat config/labs.txt)

for LAB_NAME in $LABS; do
	echo "Running stubgen for lab ${LAB_NAME}"

	for filename in ${LAB_NAME}/*.py; do
	  echo "Generating stubs for ${filename}"
    python ./config/generate_stubs/run_generator.py \
          --source_code_path ${filename} \
          --target_code_path ./build/stubs/${filename}

    echo "Checking stubgen for lab: ${LAB_NAME} file: ${filename}"

    check_if_failed
  done
done

if [[ ${FAILED} -eq 1 ]]; then
	echo "Stubgen check failed."
	exit ${FAILED}
fi

echo "Stubgen check passed."
