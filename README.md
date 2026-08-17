# GRID GUARD
**Smart Meter Security via AI-Driven Learning & Detection**

COMSATS University Islamabad — BS Computer Science 2023–2027

Supervised by: Dr. Tehsin Kanwal

## Team
- Faiza Riaz (CIIT/SP23-BCT-015/ISB) — Module 1, 4, 5
- Muhammad Umar (CIIT/SP23-BCT-040/ISB) — Module 2, 3, 6

## Project Structure
FYP/
├── module2_detection/
│ ├── data/ ← parquet files from Module 1 (not tracked)
│ ├── models/ ← trained pkl files (not tracked)
│ ├── webapp/
│ │ ├── app.py
│ │ ├── predictor.py
│ │ ├── static/
│ │ └── templates/
│ ├── main.py
│ ├── isolation_forest.py
│ ├── one_class_svm.py
│ ├── random_forest.py
│ ├── xgboost_model.py
│ ├── ensemble.py
│ └── evaluator.py
## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/GRID_GUARD.git
cd GRID_GUARD
```

### 2. Create virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install pandas numpy scikit-learn xgboost joblib pyarrow matplotlib flask
```

### 4. Add data files
Place these files in module2_detection/data/:
- train_features.parquet
- train_labels.parquet
- val_features.parquet
- val_labels.parquet
- test_features.parquet
- test_labels.parquet
- scaler.joblib
- feature_list.json

### 5. Train models
```bash
cd module2_detection
python main.py
```

### 6. Run dashboard
```bash
cd webapp
python app.py
```
Open browser at http://127.0.0.1:5000
