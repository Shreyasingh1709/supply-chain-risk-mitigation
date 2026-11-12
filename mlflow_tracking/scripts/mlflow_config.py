import mlflow

# MLflow tracking server
TRACKING_URI = "http://127.0.0.1:5000"

# Capstone experiment
EXPERIMENT_NAME = "Supply_Chain_Stockout_Prediction"


def initialize_mlflow():

    mlflow.set_tracking_uri(TRACKING_URI)

    experiment = mlflow.set_experiment(EXPERIMENT_NAME)

    print("MLflow initialized successfully")
    print("Experiment:", experiment.name)
    print("Experiment ID:", experiment.experiment_id)

    return experiment