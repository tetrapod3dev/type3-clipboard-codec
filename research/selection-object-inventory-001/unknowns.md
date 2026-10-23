# 미확정과 안전한 사용 범위

1. 선택된 최상위 객체와 내부 Serialize/Contour chain 사이의 일대일 대응이 없다. E1 UI3/chain4, F UI4/chain1이 반례다. 후보0도 실제 선택0이 아니다.
2. Group/Member의 일반 소유 경계는 UNKNOWN이다. G/H의 직렬화 tree, 정확한 Contour byte구간, 색상suffix와 UI상 두 사각형 대응을 얻었더라도 임의 혼합 그룹의 소유권을 확정하지 않는다.
3. 문자 `abcdefg`를 얻어도 glyph/기준선/shape chain 수가 독립 문자 객체 수가 아니다. E1의T1A/T2B와 geometry chain의 연결은 불확실하고 F의T2B는 누락된다. 원본 byte 전체범위도 UNKNOWN이다.
4.4record rectangle,8record circle, role 기반 polygon/polyline은 현재 classifier heuristic이다. `confirmed` 이름을 Native VERIFIED로 사용하지 않는다. bbox 동일/중복raw로 객체를 합치지 않는다.
5. color 창이 공유되는 경우 다른 member의 속성이 섞일 수 있다. 실제 G/H의 컬러가 맞아도 일반 member ownership은 UNKNOWN. Text 색상은 fixture 기록에 예상과 불일치 사례도 있다. 폰트 후보를 모든 chain에 복사하지 않는다.
6. layer·영속ID·CAM속성/참조·저장후 동일성·선택적 재조회·동일 원본 재대응은 지원하지 않는다. 표시 인덱스와 Archive ID는 해당 출력/Archive 안에서만 의미가 있다.
7. consumed range는 성공한 조건부 구조 순회 범위다. tail0 또는 tail제거도 Archive 전체 유효 길이 확인이 아니다. unknown_ranges는 원본006의 구조 미해석 범위이며 이것만 제외하면 전부 의미적으로 완성됐다는 뜻이 아니다.
8. partial/error child 결과는 성공 데이터로 사용하지 않는다. timeout/child error는 UNSUPPORTED, candidates=[]다. timeout은 단지 실행 시간 제한이며 메모리 고갈이나 OS 수준 sandbox를 완전히 해결하지 않는다. 입력16MiB상한도 형식의 유효 길이를 뜻하지 않는다.
9. PARTIAL 보고서의 exit0은 JSON/표 생성 성공이다. 완전한 객체 목록·쓰기 허가가 아니다. 기존 Decoder의 결과는 바꾸지 않는다.
10.008 Progress Guard는 PARTIAL이며17기존+4추가 실패와 frozen source lock 문제를 이 과제에서 수정하지 않았다. 전체 Suite 정상화·009는 별도 과제다.

추가 실기는 필요 여부와 범위를 결정하기 전까지 수행하지 않는다. 새 표본이 필요하다면 단독 문자2개/geometry1개/Group 혼합의 정확한 UI 선택수, 문자내용, 겹치지 않는bbox, Group전후 관계를 독립적으로 기록해야 한다. 하지만 현재 E/F가 이미 이 반례를 제공하므로 같은 표본을 다시 만드는 것을 다음 작업으로 제안하지 않는다.
