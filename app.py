from fastapi import FastAPI
import joblib
import numpy as np

app = FastAPI()

model = joblib.load("danger_detection_model.pkl")
scaler = joblib.load("scaler.pkl")

@app.get("/")
def home():
    return {"message": "Danger Detection API is running"}

@app.get("/predict")
def predict(
    heart_rate: float,
    activity_level: float,
    is_high_hr: int,
    is_high_activity: int,
    school_time: int,
    safe_zone: int
):

    features = np.array([[heart_rate,
                          activity_level,
                          is_high_hr,
                          is_high_activity,
                          hr_ratio,
                          school_time,
                          safe_zone]])

    features = scaler.transform(features)

    prediction = model.predict(features)[0]

    if prediction == 1:
        return {"prediction": "Danger"}
    else:
        return {"prediction": "Safe"}