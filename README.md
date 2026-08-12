# 전자책 자동 홍보 (auto-pr)

`content_queue.json`에 쌓인 홍보 글을 3일에 한 번씩 자동으로 Threads·Instagram에 올리는 GitHub Actions 워크플로우입니다.

## 동작 방식

1. `content_queue.json`에서 아직 안 올린(`posted: false`) 글 중 맨 위 항목 하나를 가져옵니다.
2. Threads API / Instagram Graph API로 게시합니다.
3. 성공하면 해당 항목을 `posted: true`로 바꿔서 저장소에 커밋합니다.
4. `.github/workflows/auto-post.yml`이 3일마다 자동 실행합니다 (`workflow_dispatch`로 수동 실행도 가능).

## 직접 하셔야 하는 설정 (계정 인증이라 대신할 수 없는 부분)

### 1. 인스타그램/스레드 계정을 비즈니스(또는 크리에이터) 계정으로 전환

- 인스타그램 앱 → 설정 → 계정 유형 및 도구 → "프로페셔널 계정으로 전환" → 비즈니스 선택
- 스레드는 연결된 인스타그램 계정 설정을 따라갑니다

### 2. Meta for Developers 앱 생성

1. https://developers.facebook.com 접속 → 로그인 → "내 앱" → "앱 만들기"
2. 앱 유형: "비즈니스" 선택
3. 생성된 앱에서 제품 추가 → **Threads API**, **Instagram Graph API** 두 개 추가
4. 본인 인스타그램 계정을 앱에 연결 (Instagram 테스터로 본인 계정 추가 후 초대 수락)

### 3. 액세스 토큰 발급

- Threads: 앱의 "Threads API" → "액세스 토큰 생성" 메뉴에서 단기 토큰 발급 후, 아래 안내대로 60일짜리 장기 토큰으로 교환
  ```
  GET https://graph.threads.net/access_token
      ?grant_type=th_exchange_token
      &client_secret={앱시크릿}
      &access_token={단기토큰}
  ```
- Instagram: Graph API Explorer(https://developers.facebook.com/tools/explorer/)에서 앱 선택 → 권한(`instagram_basic`, `instagram_content_publish`, `pages_show_list`) 체크 → 토큰 생성 → 마찬가지로 장기 토큰으로 교환

- **토큰은 60일마다 만료됩니다.** 만료되면 위 과정을 반복해서 GitHub Secrets 값만 갱신하면 됩니다. (완전 무기한 자동화는 아니고, 2달에 한 번 정도는 토큰 갱신이 필요해요.)

### 4. 사용자 ID 확인

- Threads User ID / Instagram User ID는 Graph API Explorer에서 `GET /me?fields=id` 호출하면 확인할 수 있습니다.

### 5. GitHub 저장소 준비

1. 이 `auto-pr` 폴더 전체를 새 GitHub 저장소로 push (공개 저장소여야 이미지 URL이 정상 작동합니다 — 표지 이미지 외 민감정보 없으니 공개해도 무방)
2. 저장소 → Settings → Secrets and variables → Actions → New repository secret 에서 아래 4개 등록
   - `THREADS_ACCESS_TOKEN`
   - `THREADS_USER_ID`
   - `IG_ACCESS_TOKEN`
   - `IG_USER_ID`

### 6. 테스트

- 저장소 → Actions 탭 → "Auto PR Post" 워크플로우 → "Run workflow" 버튼으로 수동 1회 실행해서 정상 게시되는지 확인

## 새 홍보 글 추가하기

`content_queue.json`에 아래 형식으로 항목을 추가하면 자동으로 큐에 들어갑니다.

```json
{
  "id": "고유id",
  "platform": "both",
  "text": "게시할 본문",
  "image": "images/파일명.png",
  "posted_threads": false,
  "posted_instagram": false
}
```

- `platform`: `"threads"`, `"instagram"`, `"both"` 중 선택
- `image`: 텍스트만 올릴 거면 생략 가능 (Threads는 텍스트 전용 게시 지원, Instagram은 이미지 필수)

## 출시 안내 글(launch-book1, launch-book2) 주의

큐에 이미 넣어둔 출시 안내 글은 실제 판매 링크가 아직 없어서 `note` 필드로 표시해뒀습니다. 판매 링크가 확정되면 `content_queue.json`에서 해당 항목의 `text`를 실제 링크 안내 문구로 수정한 뒤 커밋하세요.
