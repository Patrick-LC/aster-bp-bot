# ASTER–BP Hedge Bot (Python)

本倉庫包含一個「Backpack 下單 + Aster Futures 對沖」的流程腳本，以及開發過程中為了降低回歸風險而補上的自動化測試。

> 註：涉及交易/合約流程，程式碼以工程實作與測試示範為主；若要接真實資金請自行完整評估風險與權限設定。

## 這個 Repo 有什麼

- **生產腳本**：`scripts/hedge_bp_aster_futures_loop.py`
  - 兩段對沖 cycle（Leg1 / Leg2）
  - 監控成交、取消重掛、處理 API 例外
  - funding time 前的行為控制（避免時間敏感造成不確定性）
- **測試資產**：`tests/`
  - 用 `pytest` 做回歸測試
  - 用 `fakes/` 隔離外部交易所依賴、用 `fixtures/` 固化測試資料
  - 測試結果可輸出成 Allure 報告（方便 review）

## 腳本使用說明（如何設定金鑰 / 執行）

為避免 README 過長，腳本的設定與執行方式整理在：
- `README_hedge_futures.md`

## 測試與回歸（pytest）

這些測試是把開發時遇到的「不穩定/難重現情境」固定下來（例如：查單 404、成交狀態延遲、重掛後才成交、對沖下單失敗但流程仍需可預期），讓後續改動可以快速驗證行為有沒有跑掉。

### 目錄結構

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

### 執行測試

```bash
pytest -q
```

### 產出 Allure 測試資料

如果你習慣把結果視覺化/留痕，可在執行時輸出 Allure results：

```bash
pytest -q --alluredir=allure-results
```

> Allure 的 report 產生/檢視方式依你的環境與安裝而定；本倉庫會保留 `allure-results/` 的輸出格式作為結果載體。

## 對沖流程概覽

- **Leg1**：BP 以「最新價 + offset%」掛限價做空；成交後在 Aster Futures 以市價 **BUY** 對沖
- **Leg2**：BP 以「最新價 - offset%」掛限價做多；成交後在 Aster Futures 以市價 **SELL** 對沖
- **未成交處理**：持續監控 → 逾時取消 → 依最新價重掛（用於覆蓋重試/重掛/狀態機分支）
- **Funding time**：接近結算時間可停止下單（降低時間敏感的不確定性）