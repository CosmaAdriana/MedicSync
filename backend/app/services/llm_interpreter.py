"""
MedicSync — LLM Interpretation Service
Uses Google Gemini (free tier) to generate a Romanian summary of ML predictions for managers.
"""
import os
from typing import Any

import google.generativeai as genai


def interpret_staff_predictions(
    predictions: list[dict[str, Any]],
    target_date: str,
    is_holiday: bool = False,
    is_epidemic: bool = False,
    weather_temp: float = 15.0,
) -> str:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY nu este configurat. Adaugă cheia în backend/.env și repornești serverul."
        )

    genai.configure(api_key=api_key)

    available = [
        m.name for m in genai.list_models()
        if "generateContent" in m.supported_generation_methods
    ]
    if not available:
        raise RuntimeError("Nu există modele Gemini disponibile pentru această cheie API.")
    model_name = available[0]
    model = genai.GenerativeModel(model_name)

    total_patients = sum(int(p.get("predicted_patients", 0)) for p in predictions)
    total_nurses   = sum(int(p.get("recommended_nurses", 0)) for p in predictions)

    dept_lines = "\n".join(
        f"  - {p['department_name']}: {int(p['predicted_patients'])} pacienți "
        f"→ {int(p['recommended_nurses'])} asistente necesare"
        for p in sorted(predictions, key=lambda x: x.get("predicted_patients", 0), reverse=True)
    )

    context_parts = []
    if is_holiday:
        context_parts.append("zi de sărbătoare")
    if is_epidemic:
        context_parts.append("perioadă de epidemie")
    context_str = ", ".join(context_parts) if context_parts else "zi obișnuită de lucru"

    prompt = f"""Ești asistentul de management al spitalului MedicSync.
Pe baza predicțiilor generate de modelul ML, redactează un raport de maxim 4 propoziții în limba română
pentru managerul spitalului. Fii direct, profesional și folosește cifrele din date.

Data analizată: {target_date}
Context: {context_str}, temperatură estimată: {weather_temp}°C
Total pacienți estimați: {total_patients}
Total asistente necesare: {total_nurses}

Detalii per departament (descrescător după încărcare):
{dept_lines}

Raportul trebuie să:
1. Prezinte situația generală cu principalele cifre
2. Evidențieze departamentele cu cea mai mare presiune
3. Ofere o recomandare concretă managerului

Scrie raportul:"""

    response = model.generate_content(prompt)
    return response.text.strip()
