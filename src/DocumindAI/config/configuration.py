from src.DocumindAI.constants import *
from src.DocumindAI.utils.common import read_yaml,create_directories
from src.DocumindAI.entity import (DataIngestionConfig,
                                   DataValidationConfig,
                                   DataPreprocessingConfig,
                                   ModelTrainerConfig,
                                   EvaluationConfig)

class ConfigurationManager:
    def __init__(
        self,
        config_filepath = CONFIG_FILE_PATH,
        params_filepath = PARAMS_FILE_PATH):

        self.config = read_yaml(config_filepath)
        self.params = read_yaml(params_filepath)

        create_directories([self.config.artifacts_root])

    

    def get_data_ingestion_config(self) -> DataIngestionConfig:
        config = self.config.data_ingestion

        create_directories([config.root_dir])

        data_ingestion_config = DataIngestionConfig(
            root_dir=config.root_dir,
            source_URL=config.source_URL,
            local_data_file=config.local_data_file,
            unzip_dir=config.unzip_dir 
        )

        return data_ingestion_config
    
    def get_data_validation_config(self) -> DataValidationConfig:
        config = self.config.data_validation

        create_directories([config.root_dir])

        data_validation_config = DataValidationConfig(
            root_dir=config.root_dir,
            STATUS_FILE=config.STATUS_FILE,
            ALL_REQUIRED_FILES=config.ALL_REQUIRED_FILES,
        )

        return data_validation_config    
    
    def get_data_preprocessing_config(self) -> DataPreprocessingConfig:
        config = self.config.data_preprocessing
        params = self.params.preprocessing

        create_directories([config.root_dir])

        data_preprocessing_config = DataPreprocessingConfig(
            root_dir=config.root_dir,
            data_path=config.data_path,
            model = config.model,
            max_length = params.max_length,
            training_ratio = params.training_ratio,
            batch_size = params.batch_size
        )

        return data_preprocessing_config

    def get_model_trainer_config(self) -> ModelTrainerConfig:
        config = self.config.model_trainer
        params = self.params.TrainingArguments

        create_directories([config.root_dir])

        model_trainer_config = ModelTrainerConfig(
            root_dir=config.root_dir,
            data_path=config.data_path,
            model = config.model,
            num_labels = params.num_labels,
            num_train_epochs = params.num_train_epochs,
            per_device_train_batch_size = params.per_device_train_batch_size,
            per_device_eval_batch_size = params.per_device_eval_batch_size,
            learning_rate = params.learning_rate,
            eval_strategy = params.eval_strategy,
            save_strategy = params.save_strategy,
            load_best_model_at_end = params.load_best_model_at_end,
            remove_unused_columns = params.remove_unused_columns,
            gradient_accumulation_steps = params.gradient_accumulation_steps,
            weight_decay = params.weight_decay,
            optim = params.optim,
            number_of_unfreeze_layers = params.number_of_unfreeze_layers
        )

        return model_trainer_config  
    
    def get_evaluation_config(self) -> EvaluationConfig:
        config = self.config.model_evaluation
        params = self.params.TrainingArguments

        eval_config = EvaluationConfig(
            root_dir=config.root_dir,
            model_path = config.model_path,
            data_path = config.data_path,
            mlflow_uri= config.mlflow_uri,
            all_params= params
        )
        return eval_config         