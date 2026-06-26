# Taiwan Tour Planner (台灣旅遊規劃)

專為 AI Agent 設計的台灣旅遊行程規劃 Skill。(使用AI製作)

## 🌟 核心特色

1. **免費地圖與路網 (OpenStreetMap & OSRM)**：
   - 使用 **Nominatim API** 進行免費地名轉經緯度（Geocoding）。
   - 透過 **OSRM API** 計算景點間的精確交通時間（開車/步行）與距離。
   - 自動生成免費的 Google Maps 跳轉連結，完全免去 Google Maps API 的付費金鑰。
2. **離線台鐵時刻表 (SQLite 快取)**：
   - 預設對接台灣**政府資料開放平臺 (data.gov.tw)** 的鐵路時刻表數據。
   - 本地 SQLite 快取查詢，速度極快且支援完全離線查詢，擺脫 TDX API 金鑰註冊限制。
3. **強制營業時間與通勤查核**：
   - 規劃行程時，Agent 會強制上網查核每個景點的營業狀態，避免公休吃閉門羹。
   - 強制計算相鄰景點間的移動時間，並預留緩衝，確保行程合理不緊湊。
4. **個人化偏好與預算估算**：
   - 支援大自然、歷史人文、美食探索等多種風格。
   - 自動產出結構化的每日行程表與單人預估預算表。

---

## 📂 檔案結構

```text
taiwan-tour-planner/
├── SKILL.md                         # Agent 的行為指引 (System Prompt / SOP)
├── README.md                        # 本說明文件
└── scripts/
    ├── osm_routing.py               # 經緯度定位與 OSRM 路網路線時間計算
    ├── tra_sqlite_manager.py        # 離線台鐵時刻表 SQLite 下載與查詢管理工具
    └── tra_schedule.db              # (更新後產生) 本地 SQLite 時刻表資料庫
```

---

## 🛠️ 安裝與初始化

### 1. 將本 Skill 放入工作區
將 `taiwan-tour-planner` 資料夾複製到您 Agent 專案的 `.agents/skills/` 目錄下：
```text
您的工作區/
└── .agents/
    └── skills/
        └── taiwan-tour-planner/
```

### 2. 初始化台鐵時刻表資料庫
本專案的台鐵查詢使用本地 SQLite。首次使用前，請在終端機中執行以下指令來下載最新的台鐵時刻表數據：
```bash
python scripts/tra_sqlite_manager.py --update
```
*這會自動從政府開放資料平台下載最新的時刻表，並寫入 `scripts/tra_schedule.db` 中。*

---

## 🚀 腳本使用方法

### 地圖與路網時間計算 (`osm_routing.py`)
```bash
python scripts/osm_routing.py --origin "台北車站" --destination "台中車站" --mode "driving"
```
**輸出範例：**
```json
{
  "origin": "台北車站",
  "origin_coords": [25.0477, 121.5170],
  "destination": "台中車站",
  "destination_coords": [24.1372, 120.6868],
  "mode": "driving",
  "distance_km": 158.42,
  "duration_mins": 112.5,
  "google_maps_link": "https://www.google.com/maps/dir/?api=1&origin=25.0477,121.5170&destination=24.1372,120.6868&travelmode=driving"
}
```

### 查詢台鐵班次 (`tra_sqlite_manager.py`)
```bash
python scripts/tra_sqlite_manager.py --query --origin "臺北" --destination "花蓮"
```
**輸出範例：**
```json
{
  "origin": "臺北",
  "destination": "花蓮",
  "trains": [
    {
      "train_no": "208",
      "train_type": "普悠瑪",
      "departure": "08:00",
      "arrival": "10:15"
    },
    ...
  ]
}
```

---

## 🤖 喚醒 Agent 規劃行程

在與 AI 對話時，您可以直接說：
> 「**我想使用 Taiwan Tour Planner 規劃行程**」

Agent 就會自動列出填寫表單（包含起訖點、天數、交通方式、偏好與預算），並在您填妥後使用本 Skill 的腳本為您生成完美行程！
