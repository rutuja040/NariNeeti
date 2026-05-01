from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import json
import numpy as np
import pandas as pd
import shap

app = Flask(__name__)
CORS(app)

# ── Load all saved artifacts ──────────────────────────
print("Loading models...")
model_xgb  = joblib.load('model_xgb.pkl')
model_rf   = joblib.load('model_rf.pkl')
scaler     = joblib.load('scaler.pkl')
encoders   = joblib.load('encoders.pkl')
explainer  = joblib.load('explainer.pkl')

with open('feature_columns.json') as f:
    feature_cols = json.load(f)

print("All models loaded successfully!")

# ── Feature direction map ─────────────────────────────
FEATURE_DIRECTION = {
    'Fund_Release_Delay_Days'       : 'reduce',
    'Pending_Applications'          : 'reduce',
    'Rejected_Applications'         : 'reduce',
    'Processing_Time_Days'          : 'reduce',
    'Female_Unemployment_Rate'      : 'reduce',
    'Poverty_Rate_State'            : 'reduce',
    'Crime_Against_Women_Rate'      : 'reduce',
    'Funds_Utilized_Crore'          : 'increase',
    'Funds_Allocated_Crore'         : 'increase',
    'Total_Budget_Crore'            : 'increase',
    'Approved_Applications'         : 'increase',
    'Staff_Assigned'                : 'increase',
    'Monitoring_Visits_Count'       : 'increase',
    'Awareness_Campaigns_Conducted' : 'increase',
    'Digital_Application_Percentage': 'increase',
    'Skill_Training_Completed'      : 'increase',
    'Female_Literacy_Rate_State'    : 'increase',
    'Urbanization_Rate'             : 'increase',
}

ACTIONABLE = [
    'Fund_Release_Delay_Days', 'Pending_Applications',
    'Rejected_Applications', 'Processing_Time_Days',
    'Staff_Assigned', 'Awareness_Campaigns_Conducted',
    'Digital_Application_Percentage', 'Monitoring_Visits_Count',
    'Skill_Training_Completed', 'Funds_Utilized_Crore',
    'Funds_Allocated_Crore', 'Total_Budget_Crore'
]

# ── Helper: prepare input ─────────────────────────────
def prepare_input(data):
    """Convert incoming JSON to scaled numpy array"""
    df = pd.DataFrame([data])

    # encode categorical columns
    cat_cols = ['Scheme_Name', 'State', 'District', 'Quarter']
    for col in cat_cols:
        if col in df.columns and col in encoders:
            le = encoders[col]
            val = str(df[col].iloc[0])
            # handle unseen labels gracefully
            if val in le.classes_:
                df[col] = le.transform([val])
            else:
                df[col] = 0  # default for unknown

    # ensure all feature columns present in correct order
    for col in feature_cols:
        if col not in df.columns:
            df[col] = 0

    df = df[feature_cols]
    scaled = scaler.transform(df)
    return scaled, df

# ── Route 1: Health check ─────────────────────────────
@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status'      : 'ok',
        'models_loaded': True,
        'features'    : len(feature_cols)
    })

# ── Route 2: Risk prediction ──────────────────────────
@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        print("Received keys:", list(data.keys()))      # add this
        print("Expected keys:", feature_cols[:5])
        scaled, _ = prepare_input(data)

        # XGBoost prediction
        risk_prob = float(model_xgb.predict_proba(scaled)[0][1])
        risk_label = 'HIGH' if risk_prob >= 0.5 else 'LOW'

        # Risk level category
        if risk_prob >= 0.75:
            risk_category = 'Critical'
        elif risk_prob >= 0.5:
            risk_category = 'High'
        elif risk_prob >= 0.25:
            risk_category = 'Medium'
        else:
            risk_category = 'Low'

        # RF prediction for comparison
        rf_prob = float(model_rf.predict_proba(scaled)[0][1])

        return jsonify({
            'risk_probability' : round(risk_prob * 100, 2),
            'risk_label'       : risk_label,
            'risk_category'    : risk_category,
            'rf_probability'   : round(rf_prob * 100, 2),
            'model_used'       : 'XGBoost'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ── Route 3: SHAP explanation ─────────────────────────
@app.route('/explain', methods=['POST'])
def explain():
    try:
        data = request.json
        scaled, _ = prepare_input(data)

        shap_vals = explainer.shap_values(scaled)[0]

        shap_df = pd.DataFrame({
            'feature'  : feature_cols,
            'shap'     : shap_vals,
            'abs_shap' : np.abs(shap_vals)
        }).sort_values('abs_shap', ascending=False)

        top_features = []
        for _, row in shap_df.head(8).iterrows():
            top_features.append({
                'feature'  : row['feature'],
                'shap'     : round(float(row['shap']), 4),
                'abs_shap' : round(float(row['abs_shap']), 4),
                'direction': 'increases_risk' if row['shap'] > 0 else 'decreases_risk'
            })

        return jsonify({
            'top_features' : top_features,
            'base_value'   : round(float(explainer.expected_value), 4)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ── Route 4: What-if simulation ───────────────────────
@app.route('/whatif', methods=['POST'])
def whatif():
    try:
        body     = request.json
        base     = body.get('base_input')
        changes  = body.get('changes', {})

        # baseline risk
        base_scaled, _  = prepare_input(base)
        prob_before     = float(model_xgb.predict_proba(base_scaled)[0][1])

        # modified risk
        modified = base.copy()
        modified.update(changes)
        mod_scaled, _  = prepare_input(modified)
        prob_after     = float(model_xgb.predict_proba(mod_scaled)[0][1])

        delta = prob_after - prob_before

        return jsonify({
            'risk_before'    : round(prob_before * 100, 2),
            'risk_after'     : round(prob_after  * 100, 2),
            'risk_delta'     : round(delta * 100, 2),
            'improvement'    : delta < 0,
            'changes_applied': changes
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ── Route 5: Recommendations ──────────────────────────
@app.route('/recommend', methods=['POST'])
def recommend():
    try:
        data   = request.json
        scaled, _ = prepare_input(data)

        shap_vals = explainer.shap_values(scaled)[0]
        risk_prob = float(model_xgb.predict_proba(scaled)[0][1])

        shap_df = pd.DataFrame({
            'feature'  : feature_cols,
            'shap'     : shap_vals,
            'abs_shap' : np.abs(shap_vals)
        })

        # only actionable features that are currently increasing risk
        shap_df = shap_df[shap_df['feature'].isin(ACTIONABLE)]
        shap_df = shap_df[shap_df['shap'] > 0]
        shap_df = shap_df.sort_values('abs_shap', ascending=False)

        recommendations = []
        for _, row in shap_df.head(3).iterrows():
            feat      = row['feature']
            direction = FEATURE_DIRECTION.get(feat, 'reduce')
            impact    = round(float(row['abs_shap']), 4)

            action = f"Reduce {feat.replace('_', ' ')}" \
                     if direction == 'reduce' \
                     else f"Increase {feat.replace('_', ' ')}"

            recommendations.append({
                'feature'    : feat,
                'action'     : action,
                'direction'  : direction,
                'shap_impact': impact,
                'priority'   : 'High' if impact > 1 else 'Medium'
            })

        return jsonify({
            'risk_probability'  : round(risk_prob * 100, 2),
            'risk_label'        : 'HIGH' if risk_prob >= 0.5 else 'LOW',
            'recommendations'   : recommendations,
            'total_suggestions' : len(recommendations)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ── Run server ────────────────────────────────────────
if __name__ == '__main__':
    app.run(port=5001, debug=True)