@echo off
setlocal enabledelayedexpansion

if "%~1"=="" (
    echo Please use argument: smoke or another.
    exit /b 1
)

set "ARG=%~1"

if "%ARG%"=="smoke" (
    set DIRS_TO_CHECK=config seminars lab_4_retrieval_w_clustering
) else (
    set DIRS_TO_CHECK=config seminars lab_1_classify_by_unigrams lab_2_retrieval_w_bm25 lab_3_ann_retriever lab_4_retrieval_w_clustering
)

set PYTHONPATH=%cd%

for %%D in (%DIRS_TO_CHECK%) do (
    python -m pylint %%D --rcfile "pyproject.toml"
)

for %%D in (%DIRS_TO_CHECK%) do (
    python -m black --check %%D
)

for %%D in (%DIRS_TO_CHECK%) do (
    mypy %%D --config-file "pyproject.toml"
)

for %%D in (%DIRS_TO_CHECK%) do (
    python -m flake8 %%D
)

python -m pytest -m "mark10 and lab_4_retrieval_w_clustering"

if not "%ARG%"=="smoke" (
    python -m pytest -m "mark10 and lab_1_classify_by_unigrams"
    python -m pytest -m "mark10 and lab_2_retrieval_w_bm25"
    python -m pytest -m "mark10 and lab_3_ann_retriever"
    python -m pytest -m "mark10 and lab_4_retrieval_w_clustering"
)
endlocal
