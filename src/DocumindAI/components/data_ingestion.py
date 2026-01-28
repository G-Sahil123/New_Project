import os
from huggingface_hub import snapshot_download  #type:ignore
import zipfile
from src.DocumindAI.logging import logger
from src.DocumindAI.utils.common import get_size
from pathlib import Path
from src.DocumindAI.entity.config_entity import DataIngestionConfig

class DataIngestion:
    def __init__(self, config: DataIngestionConfig):
        self.config = config


    def download_file(self):
        """
        Downloads the dataset from Hugging Face Hub using snapshot_download().
        If the dataset already exists locally, it skips downloading.
        """
        dataset_dir = Path(self.config.root_dir)
        os.makedirs(dataset_dir, exist_ok=True)

        if not os.path.exists(self.config.unzip_dir) or len(os.listdir(self.config.unzip_dir)) == 0:
            logger.info(f"Downloading dataset from Hugging Face: {self.config.source_URL}")
            repo_id = self.config.source_URL.replace("https://huggingface.co/datasets/OCR_datset", "").strip("/")

            local_path = snapshot_download(
                repo_id=repo_id,
                repo_type="dataset",
                local_dir=dataset_dir,
                token=os.getenv("HF_TOKEN", None) 
            )

            logger.info(f"Dataset downloaded at: {local_path}")
        else:
            logger.info(f"Dataset already exists at {self.config.unzip_dir} (Size: {get_size(Path(self.config.unzip_dir))})")


    def extract_zip_file(self):
        unzip_path = self.config.unzip_dir
        os.makedirs(unzip_path, exist_ok=True)

        for file in os.listdir(self.config.root_dir):
            if file.endswith(".zip"):
                zip_path = os.path.join(self.config.root_dir, file)
                logger.info(f"Extracting {zip_path} to {unzip_path}")
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(unzip_path)

        logger.info("Extraction complete!")