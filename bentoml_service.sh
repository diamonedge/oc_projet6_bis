export BENTOML_HOST=0.0.0.0
export BENTOML_PORT=3000
uv run save_model.py
uv run bentoml build
uv run bentoml serve .
