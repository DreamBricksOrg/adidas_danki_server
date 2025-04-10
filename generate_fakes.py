import random
from datetime import datetime, timedelta
import json

# Categorias possíveis
categories = ["SAMBA OG", "SAMBAE", "SL 72 OG", "TAEKWONDO"]
codes = ["B75806", "JI2746", "JI2725", "JP5330", "JP5609", "Jl1349", "JS1192"]
macs = [f"6C:FD:22:76:{random.randint(0x00, 0xFF):02X}:{random.randint(0x00, 0xFF):02X}" for _ in range(20)]

# Geração dos dados
def generate_data_entry(date):
    start_hour = random.randint(10, 21)
    start_minute = random.randint(0, 59)
    start_second = random.randint(0, 59)
    start_time = datetime.strptime(date, "%Y-%m-%d") + timedelta(hours=start_hour, minutes=start_minute, seconds=start_second)
    duration_seconds = random.randint(1, 60)
    end_time = start_time + timedelta(seconds=duration_seconds)
    duration_str = str(timedelta(seconds=duration_seconds)).zfill(8)
    mac = random.choice(macs)
    code = random.choice(codes)
    category = random.choice(categories)
    uploaded_time = datetime.strptime(date + "T10:00:00", "%Y-%m-%dT%H:%M:%S") - timedelta(minutes=random.randint(10, 120))
    time_played = start_time + timedelta(minutes=random.randint(5, 30))

    return {
        "uploadedData": {"$date": uploaded_time.isoformat() + "Z"},
        "timePlayed": {"$date": time_played.isoformat() + "Z"},
        "status": "MEXEU",
        "project": {"$oid": "67f036ec948859cd9ed13796"},
        "additional": f"{mac},{start_time.isoformat()}Z,{end_time.isoformat()}Z,{duration_str},{code},{category}",
        "isr": "false"
    }

# Gerar dados
dates = ["2025-04-05", "2025-04-06"]
data = [generate_data_entry(date) for date in dates for _ in range(75)]

# Salvar em um arquivo JSON com aspas duplas e formatado
with open("dados_mongo.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)
