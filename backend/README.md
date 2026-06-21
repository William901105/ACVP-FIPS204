# Backend

FastAPI backend for the FIPS 204 / ML-DSA ACVP JSON viewer and local validator.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

