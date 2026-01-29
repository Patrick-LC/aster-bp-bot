# ASTER-BP Hedge Bot
> ⚠️ 免責聲明：本倉庫包含交易/合約相關程式碼，僅用於學習與工程實作示範；請勿在未充分理解風險前用於真實資金。

這個腳本一開始只是跑對沖流程的腳本。隨著邏輯變複雜（重試、重掛、資金費率時間、各種 API 例外），我把它補上了 **可回歸的 QA 測試**，避免每次改動都靠人工盯盤與猜測：
- **生產腳本**：Backpack（現貨）× Aster（合約）的對沖流程（含 funding time 的行為控制）
- **測試資產**：pytest + fakes/stubs 隔離外部交易所依賴，並用 Allure 輸出可讀的測試報告

---

## 🧩 腳本背景與執行方式

本倉庫主要放的是腳本本體與我在開發過程中補上的測試。

為避免 README 變得太長，關於「如何設定金鑰 / 執行合約對沖腳本」等使用說明放在：
- `README_hedge_futures.md`

---

## ✅ 測試與回歸（pytest + Allure）

### 目錄結構（測試相關）

```text
tests/
  conftest.py
  fakes/
  fixtures/
  test_hedge_logic.py
```

### 安裝測試依賴

```bash
python -m pip install -r requirements-dev.txt
```

### 執行測試並生成 Allure 資料

```bash
pytest -q --alluredir=allure-results
```

### 開啟 Allure 報告（本機臨時服務）

```bash
allure serve allure-results
```

### 生成靜態報告（用於分享/作品集）

```bash
allure generate allure-results -o allure-report --clean
```


---

## 📊 策略說明（合約對沖）

**一輪循環（Cycle）**：
1. **Leg1**：在 BP 以「最新價 + offset%」掛限價做空（Ask）；成交後在 Aster Futures 以市價 **BUY** 對沖
2. 等待 `between_legs_sleep`
3. **Leg2**：在 BP 以「最新價 - offset%」掛限價做多（Bid）；成交後在 Aster Futures 以市價 **SELL** 對沖
4. 等待 `cycle_sleep`，進入下一輪

**未成交處理**：
- 訂單持續監控；達到閾值後取消並依最新價重掛（用於示範「重試/重掛/狀態機分支」）

**Funding time**：
- 計算下一個 funding 結算時間；可在結算前 N 分鐘停止下單，以降低不確定性

---