# MedicSync Frontend - Streamlit Application

Frontend pentru platforma MedicSync Health 4.0, construit cu Streamlit pentru interfață rapidă și interactivă.

## 🚀 Quick Start

### 1. Instalare Dependințe

```bash
cd frontend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# Instalare pachete
pip install -r requirements.txt
```

### 2. Configurare Backend

Asigură-te că backend-ul FastAPI rulează pe `http://localhost:8000`

```bash
# În terminal separat, din folder-ul backend/
cd ../backend
python -m uvicorn app.main:app --reload
```

### 3. Pornire Frontend

```bash
cd streamlit_app
streamlit run app.py
```

Aplicația va fi disponibilă la: **http://localhost:8501**

---

## 📁 Structură Proiect

```
frontend/
├── streamlit_app/
│   ├── app.py                          # Entry point principal
│   ├── config.py                       # Configurări (API URL)
│   ├── api_client.py                   # Client pentru backend API
│   ├── auth.py                         # Autentificare & Session
│   │
│   ├── pages/                          # Pagini multi-page app
│   │   ├── 1_🏥_Dashboard.py          # KPIs și overview
│   │   ├── 2_🏛️_Departamente.py      # Management departamente
│   │   ├── 3_👤_Pacienți.py          # Evidență pacienți
│   │   ├── 4_💓_Semne_Vitale.py      # Monitorizare vitale + alerte
│   │   └── 5_🤖_Predicții_ML.py      # Predicții ML Health 4.0
│   │
│   └── components/                     # Componente reutilizabile
│       └── stats_cards.py              # Carduri pentru metrici
│
├── requirements.txt                    # Dependințe Python
└── README.md                           # Acest fișier
```

---

## 🔑 Autentificare

### Credențiale Demo

Pentru testare rapidă:

- **Email:** `manager@test.com`
- **Parolă:** `test123`
- **Rol:** Manager (acces complet)

### Roluri Disponibile

| Rol | Acces |
|-----|-------|
| **manager** | Acces complet + predicții ML + creare departamente |
| **doctor** | Vizualizare pacienți, semne vitale, alerte |
| **nurse** | Înregistrare semne vitale, vizualizare pacienți |
| **inventory_manager** | Management inventar, comenzi, predicții stoc |

---

## 📊 Funcționalități Principale

### 1. 🏥 Dashboard
- KPI-uri în timp real
- Grafice distribuție pacienți
- Status inventar
- Overview departamente

### 2. 🏛️ Departamente
- Listare departamente cu statistici
- Creare departamente noi (manager only)
- Vizualizare carduri per departament

### 3. 👤 Pacienți
- Filtrare după departament și status
- Internare pacienți noi
- Vizualizare detalii pacient
- Quick actions (semne vitale, alerte)

### 4. 💓 Semne Vitale & Alerte
- **Înregistrare semne vitale** (nurse only)
- **Grafice interactive** cu Plotly:
  - Evoluție puls, SpO₂, respirație
  - Tensiune arterială (sistolică/diastolică)
  - Threshold lines pentru valori critice
- **Sistem de alertare automată**:
  - Detecție anomalii în timp real
  - Nivele de risc: Critical, High, Medium, Low
  - Afișare alerte active

### 5. 🤖 Predicții ML (Health 4.0)
- **Model:** RandomForest (R²=93.37%, MAE=6.09)
- **Predicții per departament**:
  - Număr pacienți estimat
  - Personal medical necesar
- **Parametri configurabili**:
  - Dată predicție
  - Temperatură
  - Sărbătoare / Epidemie
- **Vizualizări**:
  - Comparații între departamente
  - Grafice bar grouped
  - Export CSV

---

## 🛠️ Configurare Avansată

### Variabile de Mediu

Creează `.env` în `frontend/streamlit_app/`:

```env
API_BASE_URL=http://localhost:8000
```

### Customizare Culori

Editează `streamlit_app/config.py`:

```python
PRIMARY_COLOR = "#1f77b4"
BACKGROUND_COLOR = "#ffffff"
```

---

## 🧪 Testare

### Test Manual

1. Pornește backend-ul
2. Pornește frontend-ul
3. Login cu credențiale demo
4. Testează fiecare pagină:
   - ✅ Dashboard se încarcă cu date
   - ✅ Poți crea departament nou
   - ✅ Poți interna pacient
   - ✅ Poți înregistra semne vitale
   - ✅ Predicțiile ML funcționează

---

## 📸 Screenshots

### Dashboard
![Dashboard](docs/screenshots/dashboard.png)

### Predicții ML
![Predictii ML](docs/screenshots/predictions.png)

### Semne Vitale
![Semne Vitale](docs/screenshots/vitals.png)

---

## 🐛 Troubleshooting

### Eroare: "Connection refused"
- Verifică că backend-ul rulează pe `http://localhost:8000`
- Test: `curl http://localhost:8000/ping`

### Eroare: "Not authenticated"
- Fă logout și login din nou
- Verifică că tokenul JWT nu a expirat (60 min)

### Pagina nu se încarcă
- Verifică console-ul browser pentru erori
- Reîmprospătează pagina (F5)
- Șterge cache Streamlit: `streamlit cache clear`

---

## 🚀 Deployment Production

### Backend Configuration

Editează `config.py`:

```python
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.medicsync.ro")
```

### Run with Gunicorn (Production)

```bash
# Nu se aplică pentru Streamlit - folosește streamlit run
# Pentru production, folosește Streamlit Cloud sau Docker
```

---

## 📦 Dependințe Principale

| Package | Versiune | Scop |
|---------|----------|------|
| streamlit | 1.32.0 | Framework UI |
| requests | 2.31.0 | HTTP client pentru API |
| plotly | 5.20.0 | Grafice interactive |
| pandas | 2.2.0 | Data manipulation |

---

## 📝 TODO (Îmbunătățiri Viitoare)

- [ ] Pagină Inventar (Phase 6)
- [ ] Pagină Ture Personal
- [ ] Export Excel cu grafice de tură
- [ ] React components pentru calendare avansate
- [ ] WebSocket pentru notificări real-time
- [ ] Dark mode toggle
- [ ] Multi-language support (RO/EN)

---

## 👨‍💻 Developer Notes

### Adăugare Pagină Nouă

1. Creează fișier în `pages/` cu format: `[NUMBER]_[EMOJI]_[Name].py`
2. Adaugă la început:
```python
import streamlit as st
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from auth import require_auth

st.set_page_config(page_title="...", page_icon="...", layout="wide")
require_auth(allowed_roles=["manager"])  # Optional
```

### Adăugare Endpoint API Nou

Editează `api_client.py`:

```python
def my_new_endpoint(self, param: str) -> Dict:
    """Descriere endpoint."""
    return self.get(f"/my-endpoint/{param}")
```

---

## 📞 Contact & Suport

Pentru întrebări sau probleme, contactează echipa MedicSync.

**Licență:** Proiect de licență - MedicSync Health 4.0
**An:** 2026
