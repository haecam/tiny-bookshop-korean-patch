# Tiny Bookshop 한국어 패치

Tiny Bookshop (Steam) 비공식 한국어 팬 패치입니다.
**게임 버전 1.1.6 기준**으로 제작되었습니다.

---

## 설치 방법

### 1단계 — 패치 파일 다운로드

[Releases 페이지](https://github.com/haecam/tiny-bookshop-korean-patch/releases/latest)에서 운영체제에 맞는 zip을 다운로드합니다.

- Windows: `TinyBookshop_한국어패치_win_v*.zip`
- Mac: `TinyBookshop_한국어패치_mac_v*.zip`

---

### Windows

#### 2단계 — 파일 덮어쓰기

ZIP을 압축 해제한 뒤, 파일들을 아래 경로에 **덮어쓰기**합니다.

> 관리자 권한 요청 창이 뜨면 **'계속'** 을 눌러주세요.

```
C:\Program Files (x86)\Steam\steamapps\common\Tiny Bookshop\
  Tiny Bookshop_Data\StreamingAssets\aa\StandaloneWindows64\
```

#### 3단계 — 언어 변경

Steam → 게임 우클릭 → **속성 → 언어 → Polish** 선택 후 실행

---

### Mac

#### 2단계 — 파일 덮어쓰기

ZIP 안의 `StandaloneOSX` 폴더를 열면 파일 6개가 있습니다. 이 파일들을 아래 경로에 **복사(덮어쓰기)**합니다.

Finder에서 **이동 → 폴더로 이동** (⇧⌘G) 에 아래 경로를 붙여넣으세요.

```
~/Library/Application Support/Steam/steamapps/common/Tiny Bookshop/Tiny Bookshop.app/Contents/Resources/Data/StreamingAssets/aa/StandaloneOSX
```

> `~` 는 홈 폴더(`/Users/사용자이름`)를 의미합니다.  
> `.app` 파일을 우클릭 → **패키지 내용 보기**로 접근해도 됩니다.

#### 3단계 — 언어 변경

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

## 주의사항

- 이 패치는 **Polish 언어 슬롯**을 활용합니다. 폴란드어 텍스트는 표시되지 않습니다.
- 게임 업데이트 후 **파일 무결성 검사** 또는 게임 자동 업데이트 시 패치 파일이 초기화될 수 있습니다. 그럴 경우 재적용해 주세요.
- Xbox Game Pass PC 버전은 지원하지 않습니다.
- 비공식 팬 패치이며 개발사(Bookstonbury Dev)와 무관합니다.
