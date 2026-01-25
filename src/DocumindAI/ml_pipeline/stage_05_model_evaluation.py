from src.DocumindAI.config.configuration import ConfigurationManager
from src.DocumindAI.components.model_evaluation import ModelEvaluation


class ModelEvaluationPipeline:
    def __init__(self):
        pass

    def main(self):
        config = ConfigurationManager()
        eval_config = config.get_evaluation_config()
        evaluation = ModelEvaluation(eval_config)
        evaluation.evaluation()
        evaluation.log_into_mlflow()
        evaluation.register_model()