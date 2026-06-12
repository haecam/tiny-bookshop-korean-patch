# Tiny Bookshop 한국어 패치

Tiny Bookshop (Steam) 비공식 한국어 팬 패치입니다.
**게임 버전 1.1.6 기준**으로 제작되었습니다.

---

## 설치 방법 (권장)

> Python 설치 없이 파일 2개만 교체하면 됩니다.

### 1단계 — 패치 파일 다운로드

[Releases 페이지](https://github.com/haecam/tiny-bookshop-korean-patch/releases/latest)에서 `korean-patch-v*.zip`을 다운로드합니다.

### 2단계 — 파일 덮어쓰기

ZIP을 압축 해제한 뒤, 두 파일을 아래 경로에 **덮어쓰기**합니다.

```
C:\Program Files (x86)\Steam\steamapps\common\Tiny Bookshop\
  Tiny Bookshop_Data\StreamingAssets\aa\StandaloneWindows64\
```

| 파일 | 용도 |
|------|------|
| `loca_pl_assets_all.bundle` | 번역 데이터 |
| `tmp_assets_all_0f1b704e3546a0e4d9fd806732287a87.bundle` | 한국어 폰트 |

### 3단계 — 언어 변경

Steam → 게임 우클릭 → **속성 → 언어 → Polish** 선택 후 실행

---

## 번역 현황

| 항목 | 수량 |
|------|------|
| 캐릭터 대사 | ~7,500줄 |
| 신문 기사 | 275줄 |
| UI / 아이템 텍스트 | ~3,300개 |
| 책 제목 / 설명 | ~2,800개 |

---

## 사용 폰트

- **본문 대사**: RIDIBatang (리디바탕)
- **신문 본문**: BookkMyungjo (부크크명조) Light / Bold
- **타이틀 / 손글씨**: Itim, Schoolbell

---

## 주의사항

- 이 패치는 **Polish 언어 슬롯**을 활용합니다. 폴란드어 텍스트는 표시되지 않습니다.
- 게임 업데이트 후 Steam의 **파일 무결성 검사** 또는 업데이트 시 패치 파일이 초기화될 수 있습니다. 그럴 경우 재적용해 주세요.
- 비공식 팬 패치이며 개발사(Bookstonbury Dev)와 무관합니다.

---

## 직접 빌드 (개발자용)

<details>
<summary>스크립트로 직접 패치 적용하기</summary>

### 필요 환경
```
pip install UnityPy freetype-py Pillow scipy numpy
```

### 순서 (게임 종료 상태에서 실행)

```bash
# 1. 폰트 SDF 굽기
python scripts/bake_ridibatang.py
python scripts/bake_itim_schoolbell.py
python scripts/bake_bookkmyungjo.py

# 2. 번역 주입
python scripts/inject_pl_bundle.py
python scripts/inject_pl_main.py
python scripts/inject_all_translations.py
```

이후 Steam 언어를 Polish로 변경하면 됩니다.

</details>
