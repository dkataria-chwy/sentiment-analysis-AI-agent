import yaml
from pathlib import Path
 
def load_query_template(name: str) -> str:
    config_path = Path(__file__).parent.parent / "config" / "query_templates.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return config[name]["query"] 