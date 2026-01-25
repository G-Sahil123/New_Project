from transformers import AutoProcessor, LayoutLMv3ForSequenceClassification
import torch
import numpy as np
from sklearn.metrics import accuracy_score, f1_score
import mlflow
from mlflow.tracking import MlflowClient
from src.DocumindAI.entity import EvaluationConfig
from datasets import load_from_disk
from pathlib import Path
from src.DocumindAI.utils.common import save_json


class ModelEvaluation:
    def __init__(self, config: EvaluationConfig):
        self.config = config
        self.client = MlflowClient()
        self.metrics = {}
        self.model = None

    def load_model_and_processor(self):
        self.processor = AutoProcessor.from_pretrained(
            self.config.model_path
        )

        self.model = LayoutLMv3ForSequenceClassification.from_pretrained(
            self.config.model_path
        )

        self.model.eval() 

    def load_dataset(self):
        self.dataset = load_from_disk(self.config.data_path)
        self.eval_dataset = self.dataset["test"]

    def evaluation(self):
        self.load_model_and_processor()
        self.load_dataset()
        preds, labels, confidence = [],[],[]

        with torch.no_grad():
            for batch in self.eval_dataset:

                inputs = {
                    k:torch.tensor(v).unsqueeze(0) 
                    for k,v in batch.items() if k!="labels"
                }

                outputs = self.model(**inputs)
                logits = outputs.logits
                probs = torch.softmax(logits,dim=-1)

                predicted_id = probs.argmax(dim=-1).item()
                cnf = probs.max().item()

                preds.append(predicted_id)
                confidence.append(cnf)
                labels.append(batch["labels"])

        acc = accuracy_score(labels,preds)
        f1 = f1_score(labels,preds,average="weighted")

        self.metrics = {
            "accuracy":acc,
            "f1_score":f1,
            "confidence_scores_list":confidence
        }

        self.save_metrics(self.metrics)

    def save_metrics(self,metrics):
        scores = {"f1_score": metrics["f1_score"], "accuracy": metrics["accuracy"],"mean_confidence": float(np.mean(metrics["confidence_scores_list"]))}
        save_json(path=Path(self.config.root_dir)/"metrics.json", data=scores)

    
    def log_into_mlflow(self):
        mlflow.set_tracking_uri(self.config.mlflow_uri)
        self.experiment_name = "DocuMind-LayoutLMv3"
        mlflow.set_experiment(self.experiment_name)
        
        with mlflow.start_run(run_name="layoutlmv3-training") as run:
            mlflow.log_params(self.config.all_params)
            mlflow.log_metric("accuracy",self.metrics["accuracy"])
            mlflow.log_metric("f1_score",self.metrics["f1_score"])
            mlflow.log_metric("mean_confidence",np.mean(self.metrics["confidence_scores_list"]))
            mlflow.transformers.log_model(
                transformers_model=self.model,
                artifact_path="model",
            )

            return run.info.run_id

    def register_model(self):

        experiment = self.client.get_experiment_by_name("DocuMind-LayoutLMv3")
        runs = self.client.search_runs(
            experiment_ids = [experiment.experiment_id],
            order_by =  [
                f"metrics.accuracy DESC"
            ],
            max_results=1
        )

        if not runs:
            raise RuntimeError("No runs found to register")

        best_run = runs[0]
        model_uri = f"runs:/{best_run.info.run_id}/model"

        model_version = mlflow.register_model(
            model_uri = model_uri,
            name="Registered_Model"
        )

        version = model_version.version

        self.client.set_registered_model_alias(
            name = "Registered_Model",
            alias = "champion",
            version = version
        )