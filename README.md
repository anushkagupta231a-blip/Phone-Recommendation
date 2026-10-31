# Phone-Recommendation
# Phone-Recommendation
# 📱 SmartPick AI – Personalized Smartphone Recommendation System

## 1. Project Overview

SmartPick AI is a personalized smartphone recommendation system that helps users find the best smartphone according to their budget and personal preferences.

Users can select a persona, set their maximum budget, and receive the five best-matching smartphones ranked using a weighted scoring algorithm.

The system provides different recommendations for different user needs, such as Student, Gaming, Photography, Battery Lover, and All-Rounder.

The main objective is to make smartphone selection easier, faster, and more personalized.

## 2. Problem Statement

Choosing a smartphone can be confusing because users have different budgets and requirements.

A student may prioritize affordability, battery life, and RAM, whereas a gaming user may prioritize processor performance, RAM, and battery capacity.

Traditional smartphone comparison methods do not always consider individual user preferences.

SmartPick AI addresses this problem by providing personalized smartphone recommendations using a preference-based weighted scoring system.

## 3. Key Features

* Persona-based smartphone recommendations.
* Customizable maximum budget.
* Top 5 smartphone recommendations.
* Weighted scoring algorithm.
* Different recommendation profiles:

  * Student
  * Gaming
  * Photography
  * Battery Lover
  * All-Rounder
* Smartphone ranking based on user preferences.
* Recommendation scores out of 100.
* Explanation of recommendation scores.
* Data-driven recommendations using an Excel dataset.

## 4. Technology Stack

| Technology    | Purpose                                     |
| ------------- | ------------------------------------------- |
| Python        | Core programming language                   |
| Streamlit     | Interactive web application                 |
| Pandas        | Dataset loading and processing              |
| NumPy         | Numerical calculations                      |
| Excel (.xlsx) | Smartphone dataset                          |
| Claude        | AI-assisted development and code generation |
| VS Code       | Development environment                     |

## 5. Dataset Description

The project uses an Excel dataset named:

`sic_mobile_spec_PJ1.xlsx`

The dataset contains smartphone specifications, including:

* Processor
* Smartphone name
* Rating
* Price
* Camera
* Display type
* Display size
* Battery
* Storage
* RAM
* Weight

The application processes the dataset using Pandas and uses the available specifications to calculate personalized recommendations.

The original dataset is preserved.

## 6. Recommendation Algorithm

SmartPick AI uses a weighted-sum recommendation algorithm.

The system assigns different weights to smartphone features depending on the selected persona.

The final recommendation score is calculated using:

**Weighted Score = Σ (Feature Weight × Normalized Feature Score)**

Each eligible smartphone receives a score out of 100.

### Persona-Based Preferences

| Persona       | Main Priorities                    |
| ------------- | ---------------------------------- |
| Student       | Affordability, battery, RAM        |
| Gaming        | Processor, RAM, battery            |
| Photography   | Camera, rating, display            |
| Battery Lover | Battery capacity, affordability    |
| All-Rounder   | Balanced smartphone specifications |

The system first filters smartphones according to the user's maximum budget.

It then calculates the weighted scores, ranks eligible smartphones, and displays the top five recommendations.

Missing or unavailable specifications are handled according to the implemented scoring rules.

## 7. Project Workflow

1. User opens SmartPick AI.
2. User selects a persona.
3. User sets a maximum price.
4. User clicks the Run Recommendation button.
5. The application filters eligible smartphones.
6. The weighted scoring algorithm calculates recommendation scores.
7. The application ranks the smartphones.
8. The top five recommendations are displayed.

Changing the persona changes the feature priorities and can change the recommended smartphones.

## 8. Project Folder Structure

```text
SmartPickAI/
│
├── app.py
├── inspect_data.py
├── sic_mobile_spec_PJ1.xlsx
├── requirements.txt
├── README.md
│
└── .venv/
```

Additional folders for prompt logs, notebooks, screenshots, and outputs can be included as the project develops.

## 9. Installation and Setup

### Step 1: Clone or download the project

Open the project folder in VS Code.

### Step 2: Create a virtual environment

```bash
python -m venv .venv
```

### Step 3: Activate the virtual environment

For Windows PowerShell:

```bash
.venv\Scripts\Activate.ps1
```

### Step 4: Install dependencies

```bash
python -m pip install -r requirements.txt
```

### Step 5: Run the application

```bash
python -m streamlit run app.py
```

The application will open in your browser, usually at:

`http://localhost:8501`

## 10. How to Use

1. Open the SmartPick AI application.
2. Select your preferred persona.
3. Adjust the maximum price slider.
4. Click Run Recommendation.
5. Explore the five recommended smartphones.
6. Compare results by changing the persona while keeping the same budget.

## 11. AI-Assisted Development

Claude was used as an AI-assisted development tool for:

* Generating Python code.
* Designing the application structure.
* Creating the Streamlit interface.
* Implementing data-processing logic.
* Developing the weighted recommendation algorithm.
* Debugging and improving the application.

All generated code and recommendations were reviewed and tested during development.

## 12. Future Improvements

* Add more smartphone datasets.
* Introduce advanced recommendation algorithms.
* Improve smartphone comparison features.
* Add smartphone images.
* Include real-time smartphone prices.
* Improve recommendation explanations.
* Add more user personas.

## 13. Conclusion

SmartPick AI demonstrates how Python, data processing, and weighted scoring algorithms can be combined to create a personalized recommendation system.

The application helps users make better smartphone choices by considering their individual preferences and budget.

## 14. Project Information

**Project Name:** SmartPick AI

**Project Type:** Data Science / Recommendation System

**Programming Language:** Python

**Frontend:** Streamlit

**Data Processing:** Pandas and NumPy

**Development Tool:** VS Code

**AI Development Assistant:** Claude
