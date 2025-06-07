# 🚐 docker-can-lab

Ett testverktyg för CAN-baserade system – byggt med **Python, Flask och Docker**. Projektet simulerar ett CAN-nätverk i mjukvara och visar datan i realtid via en webbaserad dashboard.

✅ **Helt körbart i Docker – ingen fysisk CAN-hårdvara krävs.**

---

## 🎯 Syfte

Det här projektet är skapat för att:
- Lära mig praktisk användning av Docker i en inbyggd kontext
- Förstå containerbaserad testmiljö för CAN-nätverk
- Förbereda inför LIA hos ITxPT och liknande organisationer

---

## ⚙️ Systemöversikt

| Komponent   | Funktion |
|-------------|----------|
| `generator/` | Genererar fejkad CAN-data (ID + payload) |
| `api/`       | Flask-API som tar emot, lagrar och exponerar data |
| `frontend/`  | Web-dashboard med realtidsuppdatering (AJAX) |
| `Docker`     | Kör allt isolerat och bärbart med `docker compose` |

---

## 🚀 Kom igång

1. Klona repot
```bash
git clone https://github.com/ditt-användarnamn/docker-can-lab.git
cd docker-can-lab
