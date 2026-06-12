# Tiny Bookshop 한국어 패치

Tiny Bookshop (Steam) 비공식 한국어 팬 패치입니다.

## 적용 방법

### 필요 환경
```
pip install UnityPy freetype-py Pillow scipy numpy
```

### 순서

1. **폰트 SDF 굽기** — 게임 종료 상태에서 실행
   ```
   python scripts/bake_ridibatang.py
   python scripts/bake_itim_schoolbell.py
   python scripts/bake_bookkmyungjo.py
   ```

2. **번역 주입** — 게임 종료 상태에서 실행
   ```
   python scripts/inject_pl_bundle.py
   python scripts/inject_pl_main.py
   python scripts/inject_all_translations.py
   ```

3. Steam에서 언어를 **Polish**로 변경 후 게임 실행

## 번역 현황

| 항목 | 수량 |
|------|------|
| 다이얼로그 (캐릭터 대사) | ~7,500줄 |
| 신문 기사 | 275줄 |
| UI / 아이템 텍스트 | ~3,300개 |
| 책 제목 / 설명 | ~2,800개 |

## 사용 폰트

- **본문 대사**: RIDIBatang (리디바탕)
- **신문 본문**: BookkMyungjo (부크크명조) Light / Bold
- **타이틀 / 손글씨**: Itim, Schoolbell

## 주의사항

- 이 패치는 **Polish** 언어 슬롯을 사용합니다.
- 게임 업데이트 시 번들 파일이 교체되어 패치가 초기화될 수 있습니다.
- 비공식 팬 패치이며 개발사와 무관합니다.
