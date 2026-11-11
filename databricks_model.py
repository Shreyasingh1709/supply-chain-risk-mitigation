import mlflow
import mlflow.pyfunc
from dotenv import load_dotenv

load_dotenv()

mlflow.set_tracking_uri("databricks")
mlflow.set_registry_uri("databricks-uc")

MODEL_URI = (
    "models:/workspace.supply_chain_db."
    "stockout_prediction_model/1"
)


def load_stockout_model():

    print("Loading registered Databricks model...")

    model = mlflow.pyfunc.load_model(MODEL_URI)

    print("Model loaded successfully!")

    return model

if __name__ == "__main__":
    model = load_stockout_model()
    print("Model is ready for prediction!")