# -*- coding: utf-8 -*-
"""t53_old26 시험 — 통과해야 차장님께 드린다"""
from __future__ import print_function
import os, sys, io, json, tempfile, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import t53_old26 as M

PASS = []
FAIL = []


def ok(name, cond, note=''):
    (PASS if cond else FAIL).append(name)
    print('  %s  %s %s' % ('OK ' if cond else 'FAIL', name, note))


def meta(site, ymd, hm, name, items, todos):
    return {'meta': {'site': site, 'ymd': ymd, 'hm': hm, 'person': name, 'company': '', 'name': name, 'rank': ''},
            'sec': {'1': {'현장': site, '안건목록': items, '일정': ['- 설치 | 260923 | 오후']},
                    '2': {'할 일': todos}}}


def main():
    tmp = tempfile.mkdtemp()
    try:
        a = meta('연합기숙사', '260922', '18:07', '홍승조 부장',
                 [{'title': '자재 입고', 'bullets': ['입고 예정일 260923', '조정 가능 여부'], 'decision': '없음 — 확인 후', 'actions': ['확인 예정 · 입고 조정']}],
                 ['- 260923 | 입고 시간 조정 확인 | 배성윤 → 건축', '- 260925 | 함 품목 확인 | 배성윤', '- 미정 | 사진 보내기 | 배성윤 → 위한빛', '- 260924 | 세 번째 날짜 할 일 | 배성윤'])
        b = meta('복합회의', '260921', '', '내부',
                 [{'title': '납품', 'bullets': ['가능 여부'], 'decision': '', 'actions': []}], [])
        c = meta('연합기숙사', '260921', '10:00', '위한빛',
                 [{'title': '코이닝', 'bullets': ['치수'], 'decision': '카톡본으로 진행', 'actions': ['확인']}], ['- 미정 | 대조 | 배성윤', '===================', '- '])
        d = meta('단양디캠프', '260910', '', '김대현', [{'title': 'x', 'bullets': ['y'], 'decision': '', 'actions': []}], [])
        for i, m in enumerate([a, b, c, d]):
            with io.open(os.path.join(tmp, '%d_meta.json' % i), 'w', encoding='utf-8') as f:
                f.write(json.dumps(m, ensure_ascii=False))
        a['meta']['title'] = 'T1'; c['meta']['title'] = 'T2'
        with io.open(os.path.join(tmp, '0_meta.json'), 'w', encoding='utf-8') as f:
            f.write(json.dumps(a, ensure_ascii=False))
        with io.open(os.path.join(tmp, '9_dup_meta.json'), 'w', encoding='utf-8') as f:     # v1.2 같은 회의 두 번 올라온 것
            f.write(json.dumps(a, ensure_ascii=False))
        with io.open(os.path.join(tmp, '_삭제요망_x_meta.json'), 'w', encoding='utf-8') as f:  # v1.2 지우라 표시한 것
            f.write(json.dumps(c, ensure_ascii=False))

        res = M.build(tmp, '260912', '260924')
        ok('기간 밖(260910) 제외', res['n'] == 3, str(res['n']))
        tabs = [r['tab'] for r in res['records']]
        ok('탭 = meta.site 그대로 (복합회의도 이름 그대로)', tabs == ['복합회의', '연합기숙사'], str(tabs))
        yh = [r for r in res['records'] if r['tab'] == '연합기숙사'][0]
        ok('같은 현장 회의 2건 → 줄 2개, 날짜순', len(yh['rows']) == 2 and yh['rows'][0][0] == '260921' and yh['rows'][1][0] == '260922')
        row = yh['rows'][1]
        ok('A 6자리 글자', row[0] == '260922')
        ok('B 시각 + 협의자', row[1].startswith('18:07  ') and '홍승조' in row[1], row[1])
        ok('C 안건 번호·내용·일정', row[2].startswith('1. 자재 입고 — 입고 예정일 260923 / 조정 가능 여부') and '[일정]' in row[2], row[2][:60])
        ok('C 끝 빈 줄 3개', row[2].endswith('\n\n\n'))
        ok('D 가장 이른 기한 (예정) 형식', row[3] == '260923(예정) 입고 시간 조정 확인 → 건축', row[3])
        ok('E 두 번째 기한', row[4] == '260924(예정) 세 번째 날짜 할 일', row[4])
        ok('F 💡 시작 + 결정·조치 (「없음 —」 은 결정 없음으로)', row[5].startswith('💡 1. 결정 없음  → 확인 예정 · 입고 조정'), row[5][:60])
        ok('F 그 밖의 할 일 = 세 번째 기한 + 기한 없는 것', '그 밖의 할 일 : 260925(예정) 함 품목 확인 / 사진 보내기 → 위한빛' in row[5], row[5])
        ok('F 끝 빈 줄 3개', row[5].endswith('\n\n\n'))
        ok('G 드라이브 폴더 링크', row[6].startswith('https://drive.google.com/drive/folders/1FWev'))
        ok('「배성윤 →」 뺌', '배성윤' not in row[3] and '배성윤' not in row[5])
        r1 = yh['rows'][0]
        ok('결정 있으면 F 에 결정 글', r1[5].startswith('💡 1. 카톡본으로 진행  → 확인'), r1[5][:40])
        ok('D 없으면 빈칸', r1[3] == '' and r1[4] == '')
        ok('v1.1 「=====」 구분선은 할 일로 안 옮김', '===' not in r1[5] and '그 밖의 할 일 : 대조' in r1[5], r1[5])
        bh = [r for r in res['records'] if r['tab'] == '복합회의'][0]
        ok('결정·조치 없으면 F 기본 글', bh['rows'][0][5].startswith('💡 결정 없음 — 확인 후 재협의'))
        ok('preview 에 담당자: 라벨 (반영모음 E열용)', '담당자:' in yh['preview'] and yh['preview'].startswith('260921'), yh['preview'][:50])
        ok('person = 첫 줄 담당자', yh['person'] == '10:00  위한빛', yh['person'])
        ok('7칸', all(len(r) == 7 for rec in res['records'] for r in rec['rows']))
        # 날짜 없는 할 일만
        # 차장님 탭 이름 표
        mpath = os.path.join(tmp, 'map.json')
        with io.open(mpath, 'w', encoding='utf-8') as f:
            f.write(json.dumps({'복합회의': '회사', '없는현장': '어디'}, ensure_ascii=False))
        res2 = M.build(tmp, '260912', '260924', M.load_tabmap(mpath))
        ok('--map 표에 있는 현장만 그 탭으로', [r['tab'] for r in res2['records']] == ['회사', '연합기숙사'], str([r['tab'] for r in res2['records']]))
        ok('--map 없으면 빈 표', M.load_tabmap(os.path.join(tmp, 'none.json')) == {})
        d0, w0 = M._todo_text('- 미정 | 사진 보내기 | 배성윤 → 위한빛')
        ok('_todo_text 미정', d0 == '' and w0 == '사진 보내기 → 위한빛', repr((d0, w0)))
        d1, w1 = M._todo_text('- 260923 | 입고 확인 | 배성윤')
        ok('_todo_text 날짜', d1 == '260923' and w1 == '입고 확인', repr((d1, w1)))
    finally:
        shutil.rmtree(tmp)
    print('\n통과 %d / 실패 %d' % (len(PASS), len(FAIL)))
    return 0 if not FAIL else 1


if __name__ == '__main__':
    sys.exit(main())
