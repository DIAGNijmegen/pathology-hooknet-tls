from dicfg import ConfigReader, build_config
from pathlib import Path

NAME = "hooknettls"
MAIN_CONFIG_PATH = Path(__file__).parent / "configs" / "config.yml"

config_reader = ConfigReader(name=NAME, main_config_path=MAIN_CONFIG_PATH)
objects = build_config(config_reader.read()["default"])
print(objects)
