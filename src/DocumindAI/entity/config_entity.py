from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class DataIngestionConfig:
    root_dir: Path
    source_URL: str
    local_data_file: Path
    unzip_dir: Path

@dataclass(frozen=True)
class DataValidationConfig:
    root_dir: Path
    STATUS_FILE: str
    ALL_REQUIRED_FILES: list    

@dataclass(frozen=True)
class DataPreprocessingConfig:
    root_dir: Path
    data_path: Path
    model: Path
    max_length: int
    training_ratio: float
    batch_size: int    

@dataclass(frozen=True)
class ModelTrainerConfig:
    root_dir: Path
    data_path: Path
    model: Path
    num_labels: int
    num_train_epochs: int
    per_device_train_batch_size: int
    per_device_eval_batch_size: int
    gradient_accumulation_steps: int
    weight_decay: float
    learning_rate: float
    eval_strategy: str
    save_strategy: str
    load_best_model_at_end: bool
    remove_unused_columns: bool
    optim: str
    number_of_unfreeze_layers : int

@dataclass(frozen=True)
class EvaluationConfig:
    root_dir: Path
    model_path: Path
    data_path: Path
    all_params: dict
    mlflow_uri: str    