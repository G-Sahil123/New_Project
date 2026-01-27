import os
from datasets import Dataset, Features, Value
from transformers import AutoProcessor
import torch
from datasets import load_from_disk
from src.DocumindAI.logging import logger
from src.DocumindAI.entity.config_entity import DataPreprocessingConfig
from PIL import Image
import json

class DataPreprocessing:
    def __init__(self, config: DataPreprocessingConfig):
        self.config = config
        self.preprocessor = AutoProcessor.from_pretrained(self.config.model,apply_ocr=True)

        self.raw_dataset = {}
        self.encoded_dataset = {}
        self.label2id = {}
        self.id2label = {}
        self.num_labels = 0

    def create_dataframe_for_split(self,split_name):
        print(f"Gathering file paths for the {split_name} split...")
        split_path = os.path.join(self.config.data_path, split_name)
        data = []

        for label_name in os.listdir(split_path):
            class_dir = os.path.join(split_path, label_name)
            if os.path.isdir(class_dir):
                for filename in os.listdir(class_dir):
                    if filename.lower().endswith(('.tif', '.tiff', '.png', '.jpg', '.jpeg')):
                        data.append({
                            'image_path': os.path.join(class_dir, filename),
                            'label': label_name,
                        })

        return data

    def load_raw_dataset(self):
        train_data = self.create_dataframe_for_split('train')
        val_data = self.create_dataframe_for_split('val')
        test_data = self.create_dataframe_for_split('test')

        self.raw_dataset = {
            'train': Dataset.from_list(train_data),
            'val': Dataset.from_list(val_data),
            'test': Dataset.from_list(test_data)
        }

        self.raw_dataset['train'] = self.raw_dataset['train'].shuffle(seed=42).select(range(1800))
        self.raw_dataset['val'] = self.raw_dataset['val'].shuffle(seed=42).select(range(600))
        self.raw_dataset['test'] = self.raw_dataset['test'].shuffle(seed=42).select(range(600))

        print("\n✅ Raw datasets loaded and shuffled.")  

    def encode_labels(self):
        label_list = sorted(list(set(self.raw_dataset['test']['label'])))
        self.label2id = {label: i for i, label in enumerate(label_list)}
        self.num_labels = len(label_list)
        self.id2label = {i:label for label,i in self.label2id.items()}
        with open(os.path.join("config","id2label.json"), "w") as f:
            json.dump(self.id2label, f, indent=4)

        print(f"\nDetected Labels ({self.num_labels}): {label_list}")

        def map_label_to_id(examples):
            examples['labels'] = [self.label2id[label] for label in examples['label']]
            return examples

        self.raw_dataset = {
            split: self.raw_dataset[split].map(map_label_to_id, batched=True)
            for split in self.raw_dataset
        }

    def preprocess_data(self, examples):
        images = [Image.open(path).convert("RGB") for path in examples['image_path']]
        encoding = self.preprocessor(
            images=images,
            padding="max_length",
            truncation=True,
            max_length=self.config.max_length,
            return_tensors="pt"
        )
        encoding['labels'] = torch.tensor(examples['labels'], dtype=torch.long)
        return encoding

    def apply_preprocessing(self):
        print("\nApplying LayoutLMv2 Processor (OCR, Fusion, and Tokenization)...")
        for split_name, ds in self.raw_dataset.items():
            self.encoded_dataset[split_name] = ds.map(
                self.preprocess_data,
                batched=True,
                batch_size=self.config.batch_size,
                remove_columns=ds.column_names,
                desc=f"Preprocessing {split_name} Split"
            )
            self.encoded_dataset[split_name].set_format(type="torch")

        print("\n✅ Preprocessing complete.")
        print(f"Number of classes: {self.num_labels}")

    def save_datasets(self, save_raw_path, save_encoded_path):
        os.makedirs(save_raw_path, exist_ok=True)
        os.makedirs(save_encoded_path, exist_ok=True)

        print("\nSaving encoded datasets...")
        for split_name, ds in self.encoded_dataset.items():
            ds.save_to_disk(f"{save_encoded_path}/{split_name}")
        print("✅ Encoded dataset saved successfully!")

        print("\nSaving raw datasets...")
        for split_name, ds in self.raw_dataset.items():
            ds.save_to_disk(f"{save_raw_path}/{split_name}")
        print("✅ Raw dataset saved successfully!")   

    def preprocess(self):
        self.load_raw_dataset()
        self.encode_labels()
        self.apply_preprocessing()
    
        base_dir = self.config.root_dir
    
        self.save_datasets(
            save_raw_path=os.path.join(base_dir, "raw_dataset"),
            save_encoded_path=os.path.join(base_dir, "encoded_data")
        )

        # Save preprocessor separately
        preprocessor_dir = os.path.join(base_dir, "preprocessor")
        os.makedirs(preprocessor_dir, exist_ok=True)
        self.preprocessor.save_pretrained(preprocessor_dir)

        print(f"✅ Preprocessor saved at: {preprocessor_dir}")