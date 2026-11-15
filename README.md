# FreshCart Pipelines

Data engineering assignment workspace for the FreshCart ELT, Mage Iris, and
RabbitMQ exercises.

## Repository layout

```text
freshcart-pipelines/
├── .github/workflows/ci.yml
├── mage/
├── sql/
├── src/
├── stream/
├── tests/
├── requirements.txt
└── README.md
```

## Local setup

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
pytest -q
```

Snowflake credentials are supplied at runtime through Google Colab Secrets or
environment variables. Do not commit passwords, tokens, private keys, `.env`
files, generated landing data, or model artifacts.

## Git and CI experiments

The normal workflow is:

```powershell
git status
git add <files>
git commit -m "Describe the change"
git push origin main
```

A local commit is visible only on the local machine until it is pushed. A
temporary failing test can be used to demonstrate a red GitHub Actions run:

1. Change an assertion in `tests/test_prepare_data.py` so it is false.
2. Commit and push the experiment.
3. Capture the red workflow run.
4. Restore the assertion, run `pytest -q`, commit, and push the final green run.

Never leave the deliberately failing experiment on the final branch.

