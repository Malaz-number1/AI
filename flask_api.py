"""
Safe Kids Wearable Device - Flask API Deployment
REST API for real-time danger prediction
Author: Graduation Project Team
Date: February 2026

This API receives raw sensor data from the device and returns predictions
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import numpy as np
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests


# ============================================
# Step 1: Load Trained Models
# ============================================

print("Loading trained models...")

model = joblib.load('models/best_model_random_forest.pkl')
scaler = joblib.load('models/scaler.pkl')
feature_names = joblib.load('models/feature_names.pkl')

print("All models loaded successfully!")
print()


# ============================================
# Step 2: Feature Extraction Function
# ============================================

def extract_features(raw_data):
    """
    Convert raw sensor data to model features
    
    Raw data from device:
    - heart_rate: int (BPM)
    - accelerometerX: float (G)
    - accelerometerY: float (G)
    - accelerometerZ: float (G)
    - latitude: float
    - longitude: float
    - timestamp: str (ISO format)
    - age: int (child's age)
    - condition: str (normal/autism/adhd)
    - location_name: str (home/school/playground/transit)
    
    Returns:
    - Dictionary with all required features for model
    """
    
    # Extract basic data
    heart_rate = raw_data.get('heart_rate', 80)
    accel_x = raw_data.get('accelerometerX', 0)
    accel_y = raw_data.get('accelerometerY', 0)
    accel_z = raw_data.get('accelerometerZ', 0)
    age = raw_data.get('age', 8)
    
    # Calculate activity level from accelerometer
    # Formula: magnitude of acceleration vector
    activity_level = np.sqrt(accel_x**2 + accel_y**2 + accel_z**2)
    
    # Scale to 0-100 range (approximate)
    # Normal walking ~2-3G, running ~4-6G, intense activity ~6-10G
    activity_level = min(100, (activity_level / 10.0) * 100)
    
    # Extract time features from timestamp
    timestamp = raw_data.get('timestamp', datetime.now().isoformat())
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    except:
        dt = datetime.now()
    
    hour = dt.hour
    
    # Derived features
    is_high_hr = 1 if heart_rate > 110 else 0
    is_high_activity = 1 if activity_level > 60 else 0
    hr_to_activity_ratio = heart_rate / (activity_level + 1)  # +1 to avoid division by zero
    is_school_time = 1 if 8 <= hour < 15 else 0
    
    # Location-based features
    location_name = raw_data.get('location_name', 'unknown')
    in_safe_zone = 1 if location_name in ['home', 'school'] else 0
    
    # Encode condition (normal=0, autism=1, adhd=2)
    condition = raw_data.get('condition', 'normal')
    condition_map = {'normal': 0, 'autism': 1, 'adhd': 2}
    condition_encoded = condition_map.get(condition, 0)
    
    # Encode location (home=0, school=1, playground=2, transit=3)
    location_map = {'home': 0, 'school': 1, 'playground': 2, 'transit': 3}
    location_encoded = location_map.get(location_name, 0)
    
    # Create feature dictionary matching training features
    features = {
        'heart_rate': heart_rate,
        'activity_level': activity_level,
        'age': age,
        'hour': hour,
        'is_high_hr': is_high_hr,
        'is_high_activity': is_high_activity,
        'hr_to_activity_ratio': hr_to_activity_ratio,
        'is_school_time': is_school_time,
        'in_safe_zone': in_safe_zone,
        'condition_encoded': condition_encoded,
        'location_encoded': location_encoded
    }
    
    return features


def prepare_for_prediction(features_dict):
    """
    Prepare features for model prediction
    
    Returns:
    - Numpy array in correct order for model
    """
    # Ensure features are in correct order
    feature_values = [features_dict.get(name, 0) for name in feature_names]
    
    # Convert to numpy array and reshape for single prediction
    X = np.array(feature_values).reshape(1, -1)
    
    # Scale features
    X_scaled = scaler.transform(X)
    
    return X_scaled


# ============================================
# Step 3: API Endpoints
# ============================================

@app.route('/', methods=['GET'])
def home():
    """
    API home endpoint - health check
    """
    return jsonify({
        'status': 'running',
        'message': 'Safe Kids API is running',
        'version': '1.0',
        'endpoints': {
            'prediction': '/api/predict',
            'health': '/api/health'
        }
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    return jsonify({
        'status': 'healthy',
        'model_loaded': model is not None,
        'scaler_loaded': scaler is not None,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/predict', methods=['POST'])
def predict():
    """
    Main prediction endpoint
    
    Expected JSON format:
    {
        "heart_rate": 85,
        "accelerometerX": 1.5,
        "accelerometerY": 1.2,
        "accelerometerZ": 1.0,
        "latitude": 30.0444,
        "longitude": 31.2357,
        "timestamp": "2026-02-08T14:30:00",
        "age": 8,
        "condition": "normal",
        "location_name": "school"
    }
    
    Returns:
    {
        "prediction": "normal" or "danger",
        "confidence": 0.95,
        "risk_level": "low/medium/high/critical",
        "features_extracted": {...},
        "timestamp": "..."
    }
    """
    
    try:
        # Get JSON data from request
        raw_data = request.get_json()
        
        if not raw_data:
            return jsonify({
                'error': 'No data provided',
                'message': 'Please send JSON data with sensor readings'
            }), 400
        
        # Validate required fields
        required_fields = ['heart_rate', 'accelerometerX', 'accelerometerY', 'accelerometerZ']
        missing_fields = [field for field in required_fields if field not in raw_data]
        
        if missing_fields:
            return jsonify({
                'error': 'Missing required fields',
                'missing': missing_fields,
                'required': required_fields
            }), 400
        
        # Extract features from raw data
        features_dict = extract_features(raw_data)
        
        # Prepare for prediction
        X_scaled = prepare_for_prediction(features_dict)
        
        # Make prediction
        prediction = model.predict(X_scaled)[0]
        prediction_proba = model.predict_proba(X_scaled)[0]
        
        # Get confidence (probability of predicted class)
        confidence = float(prediction_proba[prediction])
        
        # Determine risk level
        danger_probability = float(prediction_proba[1])
        if danger_probability < 0.3:
            risk_level = 'low'
        elif danger_probability < 0.6:
            risk_level = 'medium'
        elif danger_probability < 0.85:
            risk_level = 'high'
        else:
            risk_level = 'critical'
        
        # Prepare response
        response = {
            'prediction': 'danger' if prediction == 1 else 'normal',
            'confidence': round(confidence, 4),
            'probabilities': {
                'normal': round(float(prediction_proba[0]), 4),
                'danger': round(float(prediction_proba[1]), 4)
            },
            'risk_level': risk_level,
            'features_extracted': features_dict,
            'raw_data_received': {
                'heart_rate': raw_data.get('heart_rate'),
                'activity_magnitude': round(features_dict['activity_level'], 2),
                'location': raw_data.get('location_name', 'unknown')
            },
            'timestamp': datetime.now().isoformat(),
            'alert': prediction == 1  # True if danger detected
        }
        
        # Add recommendations if danger detected
        if prediction == 1:
            response['recommendations'] = generate_recommendations(features_dict, danger_probability)
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Prediction failed',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


def generate_recommendations(features, danger_prob):
    """
    Generate recommendations based on detected danger
    """
    recommendations = []
    
    if features['is_high_hr']:
        recommendations.append("Elevated heart rate detected - check child immediately")
    
    if features['is_high_activity']:
        recommendations.append("High activity level - verify situation")
    
    if not features['in_safe_zone']:
        recommendations.append("Child outside safe zone - locate immediately")
    
    if danger_prob > 0.9:
        recommendations.append("CRITICAL: High danger probability - take immediate action")
    elif danger_prob > 0.7:
        recommendations.append("HIGH ALERT: Potential danger situation")
    
    if features['hour'] >= 22 or features['hour'] <= 6:
        recommendations.append("Unusual activity during sleep hours")
    
    return recommendations


# ============================================
# Step 4: Batch Prediction Endpoint (Optional)
# ============================================

@app.route('/api/predict/batch', methods=['POST'])
def predict_batch():
    """
    Batch prediction for multiple readings
    
    Expected JSON format:
    {
        "readings": [
            {...sensor_data_1...},
            {...sensor_data_2...},
            ...
        ]
    }
    """
    
    try:
        data = request.get_json()
        readings = data.get('readings', [])
        
        if not readings:
            return jsonify({
                'error': 'No readings provided',
                'message': 'Please send array of sensor readings'
            }), 400
        
        results = []
        
        for reading in readings:
            # Extract features
            features_dict = extract_features(reading)
            
            # Prepare for prediction
            X_scaled = prepare_for_prediction(features_dict)
            
            # Make prediction
            prediction = model.predict(X_scaled)[0]
            prediction_proba = model.predict_proba(X_scaled)[0]
            
            results.append({
                'prediction': 'danger' if prediction == 1 else 'normal',
                'confidence': round(float(prediction_proba[prediction]), 4),
                'danger_probability': round(float(prediction_proba[1]), 4),
                'timestamp': reading.get('timestamp', datetime.now().isoformat())
            })
        
        return jsonify({
            'total_readings': len(readings),
            'results': results,
            'summary': {
                'normal_count': sum(1 for r in results if r['prediction'] == 'normal'),
                'danger_count': sum(1 for r in results if r['prediction'] == 'danger')
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Batch prediction failed',
            'message': str(e)
        }), 500


# ============================================
# Run Flask App
# ============================================

if __name__ == '__main__':
    print("="*80)
    print("Safe Kids API Server Starting...")
    print("="*80)
    print()
    print("API Endpoints:")
    print("  GET  /              - API home")
    print("  GET  /api/health    - Health check")
    print("  POST /api/predict   - Single prediction")
    print("  POST /api/predict/batch - Batch predictions")
    print()
    print("Server running on: http://localhost:5000")
    print("="*80)
    print()
   """ 
    # Run the Flask app
    app.run(
        host='0.0.0.0',  # Listen on all network interfaces
        port=5000,
        debug=False  # Set to False in production
    )
    """
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)