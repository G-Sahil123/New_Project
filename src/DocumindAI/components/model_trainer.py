import os
import torch
from datasets import load_from_disk
from transformers import LayoutLMv3ForSequenceClassification
from transformers import TrainingArguments, Trainer, AutoProcessor
from src.DocumindAI.entity.config_entity import ModelTrainerConfig

class ModelTrainer:
    def __init__(self, config:ModelTrainerConfig):
        self.config = config
        self.model = None   
        self.preprocessor = AutoProcessor.from_pretrained(self.config.model,apply_ocr=True)   

    def load_encoded_dataset(self):
        print("Loading encoded dataset from disk")
        base_path = self.config.data_path

        self.encoded_dataset = {
            'train': load_from_disk(os.path.join(base_path, "train")),
            'val': load_from_disk(os.path.join(base_path, "val")),
            'test': load_from_disk(os.path.join(base_path, "test"))
        }

        for split_name in self.encoded_dataset:
            self.encoded_dataset[split_name].set_format(type='torch')

        print("✅ Encoded dataset successfully loaded and formatted!")

    def initialize_model(self):
        print("Initializing LayoutLMv3 model")

        self.model = LayoutLMv3ForSequenceClassification.from_pretrained(
            self.config.model,
            num_labels=self.config.num_labels
        )

        print("✅ Model initialized successfully!")

    def unfreeze_layers(self):

        for param in self.model.parameters():
            param.requires_grad = False

        for param in self.model.classifier.parameters():
            param.requires_grad = True

        n = self.config.number_of_unfreeze_layers
        for layer in self.model.layoutlmv3.encoder.layer[-n:]:
            for param in layer.parameters():
                param.requires_grad = True       

    def setup_trainer(self):
        print("Creating Trainer instance")
        self.training_args = TrainingArguments(
            output_dir = "",
            num_train_epochs=self.config.num_train_epochs,
            per_device_train_batch_size=self.config.per_device_train_batch_size,
            per_device_eval_batch_size=self.config.per_device_eval_batch_size,
            gradient_accumulation_steps = self.config.gradient_accumulation_steps,
            weight_decay = self.config.weight_decay,
            learning_rate=self.config.learning_rate,
            eval_strategy=self.config.eval_strategy,
            save_strategy=self.config.save_strategy,
            load_best_model_at_end=self.config.load_best_model_at_end,
            remove_unused_columns=self.config.remove_unused_columns,
            optim = self.config.optim,
            report_to=None
        )
        self.trainer = Trainer(
            model=self.model,
            args=self.training_args,
            train_dataset=self.encoded_dataset["train"],
            eval_dataset=self.encoded_dataset["val"],
        )
        print("Trainer ready!")

    def train_model(self):
        print("Starting model training...")
        self.trainer.train()
        print("Training completed!")

    def save_model(self):
        model_dir = os.path.join(self.config.root_dir,"documind_model")
        os.makedirs(model_dir, exist_ok=True)

        print(f"Saving model to: {model_dir}")
        self.preprocessor.save_pretrained(model_dir)
        self.trainer.save_model(model_dir)
        print("Model and trainer saved successfully!")

    def train(self):
        print("Running full model training pipeline")
        self.load_encoded_dataset()
        self.initialize_model()
        self.unfreeze_layers()
        self.setup_trainer()
        self.train_model()
        self.save_model()
        print(" Model training pipeline completed successfully!")
