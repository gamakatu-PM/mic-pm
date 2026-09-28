# -*- coding: utf-8 -*-
"""종합 제안서(5성급) 만들기 - 제안서_내용 25건에서 5성급에 맞는 장만 골라 한 벌로 묶는다.
(2026-09-28 프로님 : "만들어 놓은 PPT를 1개로 합쳐서 제출 할 수 있는 제안서로. 5성급 기준")

원칙
- 글은 각 제안서(문체 규칙 적용판)에서 그대로 가져온다. 새 사실을 넣지 않는다.
- 5성급 제출본이므로 1~3성급 · 리조트 비교 문구만 뺀다 (OVR 에 한 줄씩 적어 둠).
- 요청 장은 마지막 한 장으로 모은다 (5개까지 들어감).
돌리면 제안서_내용/00_종합_5성급_객실관리제안서.json 을 새로 쓴다.
"""
import io, os, json, copy

HERE = os.path.dirname(os.path.abspath(__file__))
SD = os.path.join(HERE, '..', '코드', 'km_tools', '제안서_내용')
OUT = os.path.join(SD, '00_종합_5성급_객실관리제안서.json')

# (장 묶음, 목차 설명, [(파일, 장 제목), ...])
PARTS = [
    ('회사 · 납품 실적', '5성급 호텔 납품 실적 · 마감 사례', [
        ('금1_납품레퍼런스', '실적 개요'),
        ('금1_납품레퍼런스', '주요 납품 실적 (1/2)'),
        ('금1_납품레퍼런스', '주요 납품 실적 (2/2)'),
        ('금1_납품레퍼런스', '마감 사례')]),
    ('시스템 개요', '기능 · 고객 동선별 동작 · 계통 구성', [
        ('월1_4-5성급_운영시나리오', '시스템 기능'),
        ('월4_PMS연동_운영시나리오', '고객 동선별 시스템 동작'),
        ('월4_PMS연동_운영시나리오', '시스템 구성 · PMS~객실')]),
    ('5성급 객실 구성', '위치별 기구물 · 스위트 · 주거약자실', [
        ('화2_4-5성급_객실배치', '4~5성급 구성'),
        ('화2_4-5성급_객실배치', '위치별 기구물'),
        ('화5_평면_기구물마킹', '4~5성급 기구물 위치'),
        ('화3_스위트거실형_객실배치', '스위트 구성'),
        ('화5_평면_기구물마킹', '스위트 · 거실형 기구물 위치'),
        ('화4_주거약자실_객실배치', '일반실과 차이'),
        ('화5_평면_기구물마킹', '주거약자실 기구물 위치')]),
    ('제품 · 디자인', '디자인 기준 · 계열 · BSP · 챠임벨 · 키센서', [
        ('목1_2000M_디자인카탈로그', '디자인 기준'),
        ('목1_2000M_디자인카탈로그', '시리즈별 특징'),
        ('목2_BSP_사양카드', 'BED SIDE PANEL 사양'),
        ('목3_챠임벨_키센서_디자인', '입구 INDICATOR(챠임벨) · KEY SENSOR')]),
    ('설비 연동', '에어컨 · 바닥난방 · PMS', [
        ('목5_에어컨EHP_연동설명', '에어컨(EHP) 연동 구성'),
        ('목6_바닥난방_연동설명', '바닥난방 연동 구성'),
        ('월4_PMS연동_운영시나리오', 'PMS 연동 전 확정 사항')]),
    ('운영', '층별 FIP · 방재실 운영 PC', [
        ('수1_FIP_사용매뉴얼', 'FIP 개요'),
        ('수1_FIP_사용매뉴얼', '객실 상태'),
        ('수2_방재실_운영PC매뉴얼', '화면 구성')]),
    ('공사 구분 · 인계', '공사 범위 · 타 공종 조건 · 시운전 · A/S', [
        ('월5_공사한계_업무스코프', '공사 범위 요약'),
        ('월5_공사한계_업무스코프', '공종별 담당 구분'),
        ('월5_공사한계_업무스코프', '타 공종 요청 조건'),
        ('수4_준공인계_매뉴얼', '시운전 완료 확인'),
        ('수4_준공인계_매뉴얼', '인계 후 관리')]),
]


def _row(sl, first):
    for r in sl['rows']:
        if r[0] == first:
            return r
    raise KeyError(first)


def ovr(key, sl):
    """5성급 제출본에 맞게 1~3성급 · 리조트 비교 문구만 뺀다. 이전 값은 원본 파일에 그대로 있음."""
    if key == ('화2_4-5성급_객실배치', '4~5성급 구성'):
        sl['title'] = '5성급 객실 구성'
        sl['headline'] = '문 입구 K + DM, 침대 옆 BSP 일체형, 화장실 · 베란다 조명 객실관리 제어.'   # 전: 1~3성급과 차이 : …
    elif key == ('화2_4-5성급_객실배치', '위치별 기구물'):
        _row(sl, '화장실')[3] = '객실관리 제어'                                           # 전: 1~3성급은 전기공사
        _row(sl, '거실 입구')[3] = '거실이 있을 때'                                        # 전: 성급 공통
    elif key == ('화5_평면_기구물마킹', '4~5성급 기구물 위치'):
        sl['title'] = '5성급 기구물 위치'
    elif key == ('목2_BSP_사양카드', 'BED SIDE PANEL 사양'):
        sl['pill'] = '5성급 침대 옆 표준'
        _row(sl, '적용 성급')[1] = '5성급 객실 표준'                                        # 전: 4~5성급 표준. 1~3성급 : …
    elif key == ('목3_챠임벨_키센서_디자인', '입구 INDICATOR(챠임벨) · KEY SENSOR'):
        r = _row(sl, '성급 구분')
        r[0], r[1], r[2] = '구성', '입구 INDICATOR', 'KEY SENSOR + DM PLATE'              # 전: 1~3성급 : K / 4~5성급 : K + DM
        sl['rows'] = [x for x in sl['rows'] if x[0] != '리조트']                            # 전: 리조트 행 (DM 제외)
        sl.pop('note', None)                                                              # 전: DM PLATE 4~5성급만 · 리조트 제외
    elif key == ('화4_주거약자실_객실배치', '일반실과 차이'):
        sl['title'] = '주거약자실 구성'                                                    # 이 묶음에서는 무엇과 차이인지 안 보여서
    elif key == ('화5_평면_기구물마킹', '주거약자실 기구물 위치'):
        for b in sl['boxes']:                                                             # 5성급 : 문 입구 K + DM, 침대 옆 BSP
            if b.get('id') == 'm2':
                b['title'] = '② K + DM'                                                   # 전: ② K (+DM)
            elif b.get('id') == 'm4':
                b['title'] = '④ BSP (낮춤)'                                               # 전: ④ 온도 + L (낮춤)
    elif key == ('월1_4-5성급_운영시나리오', '시스템 기능'):
        sl.pop('banner', None)                                                            # 수량·금액 줄은 마지막 요청 장 위에서 한 번만
    return sl


REQUEST = {
    'type': 'request',
    'title': '요청 사항',
    'items': [
        {'text': '객실 타입별 단위세대 평면도 공유 필요', 'desc': '스위트 · 주거약자실 포함, 기구물 구성 · 수량 확정용'},
        {'text': '전등 설계(회로 구성) 공유 필요', 'desc': '조명 스위치 구수 확정용'},
        {'text': '인테리어 마감 방향(재질 · 색상) · 목업룸 일정 공유 필요'},
        {'text': 'PMS · 도어락 · 에어컨 · 바닥난방 업체 담당자 연결 필요', 'desc': '연동 조건 3자 협의로 확정'},
        {'text': '준공 · 인계 예정일 공유 필요', 'desc': '수량 · 금액 : 별도 견적서 제출'},
    ],
}


def load(name):
    return json.loads(io.open(os.path.join(SD, name + '.json'), encoding='utf-8-sig').read())


def make():
    cache, slides, toc = {}, [], []
    for part, desc, picks in PARTS:
        first = None
        for f, t in picks:
            d = cache.setdefault(f, load(f))
            hit = [s for s in d['slides'] if s.get('title') == t]
            if len(hit) != 1:
                raise SystemExit('못 찾음 : %s / %s (%d)' % (f, t, len(hit)))
            sl = ovr((f, t), copy.deepcopy(hit[0]))
            slides.append(sl)
            first = first or sl['title']
        toc.append({'text': part, 'desc': desc, 'goto': first})
    spec = {
        '요일': '종합 · 제출용 (5성급)',
        '파일명': '객실관리 시스템 제안서',
        'title': '객실관리 시스템 제안서',
        'footer': '한국마이크로닉(주)  ·  객실관리 시스템',
        'slides': [{'type': 'cover', 'eyebrow': '객실관리 시스템',
                    'title': '{{현장_제목}}객실관리 시스템 제안서',
                    'meta': '한국마이크로닉(주)   |   {{날짜}}'},
                   {'type': 'toc', 'title': '목차', 'eyebrow': '객실관리 시스템', 'items': toc}]
                  + slides + [REQUEST],
    }
    titles = [s.get('title') for s in spec['slides']]
    dup = sorted(set(t for t in titles if titles.count(t) > 1))
    if dup:
        raise SystemExit('장 제목이 겹침 (목차 연결이 틀어짐) : %s' % dup)
    with io.open(OUT, 'w', encoding='utf-8', newline='\n') as fp:
        json.dump(spec, fp, ensure_ascii=False, indent=1)
        fp.write('\n')
    return OUT, len(spec['slides'])


if __name__ == '__main__':
    print(*make())
