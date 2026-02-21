import pandas as pd
import sklearn
from sklearn.linear_model import LinearRegression

print("Salut! Mediul de lucru pentru MedicSync este configurat corect.")
print(f"Versiunea Scikit-learn instalata: {sklearn.__version__}")

model = LinearRegression()
print("Modelul de AI a fost incarcat cu succes!")