# 🛡️ FraudShield — Credit Card Fraud Detection

FraudShield is a Machine Learning-based web application built with **Python, Flask, and Random Forest** to identify potentially fraudulent credit card transactions.

The application supports individual transaction predictions and batch CSV analysis through a simple web interface.

## 🚀 Features

- **Single Transaction Prediction:** Analyze an individual transaction.
- **Batch CSV Analysis:** Upload a CSV file to analyze multiple transactions.
- **Machine Learning:** Uses a trained Random Forest model.
- **Feature Processing:** Uses saved preprocessing components for model input.
- **Fraud Detection Dashboard:** Simple web interface built with HTML, CSS, and JavaScript.
- **Threshold-Based Prediction:** Uses a saved prediction threshold.

## 🛠️ Tech Stack

- Python
- Flask
- Scikit-learn
- Pandas
- NumPy
- HTML, CSS, JavaScript
- Random Forest Classifier

## 📂 Project Structure

```text
FraudShield-Credit-Card-Detection/
├── app.py
├── fraud_detection.py
├── fraud_model.pkl
├── fraud_features.pkl
├── fraud_threshold.pkl
├── requirements.txt
├── templates/
├── .gitignore
└── README.md
```

## ⚙️ Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/ashish-coding-hub/FraudShield-Credit-Card-Detection.git
```

### 2. Open the project folder

```bash
cd FraudShield-Credit-Card-Detection
```

### 3. Create a virtual environment (optional)

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the application

```bash
python app.py
```

Open your browser and visit:

```text
http://127.0.0.1:5000
```

## 📊 How It Works

1. The user enters transaction details or uploads a CSV file.
2. The application processes the input using the saved feature-processing components.
3. The trained Random Forest model predicts whether transactions may be fraudulent.
4. The application displays the prediction results.

**Note:** Model predictions are estimates and should not be treated as definitive proof of fraud.

## 🔒 Dataset & Privacy

The original `creditcard.csv` dataset is excluded from the repository. Do not upload sensitive financial or personal information to a public repository.

## 👨‍💻 Author

**Ashish Singh**

- GitHub: [ashish-coding-hub](https://github.com/ashish-coding-hub)
- LinkedIn: [Ashish Singh](https://www.linkedin.com/in/ashish-singh-4012ab342/)

---

⭐ If you find this project interesting, consider starring the repository!
