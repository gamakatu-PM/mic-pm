# -*- coding: utf-8 -*-
"""
새창 자가진단  (km_tools 밖, 인수인계함 전용)   AI 사용량 0

차장님 지시 (2026-09-28 밤) : 「인수인계를 잘 하는 코드를 짜」 —
새 창이 첫 답변을 하기 전에 반드시 이것부터 돌려서, 그 출력을 차장님께 그대로 보여준다.
새 창이 "읽었습니다"라고 말로만 하는 것과, 실제로 최신 상태를 붙잡고 있는지를
차장님이 코드 출력 한 번으로 바로 대조할 수 있게 하는 것이 목적이다.
읽은 내용을 새 창이 요약·재구성하면 그 요약 자체가 틀릴 수 있으므로,
아래 출력은 파일에서 그대로 오려낸 것들이다(지어내거나 줄여쓰지 않는다).

    python3 새창_자가진단.py

찍는 것 :
  1) 이 저장소 브랜치·최신 커밋 3개
  2) 인수인계함에서 번호가 가장 큰 2_창이어가기_vN_*.md 파일명
  3) 그 파일의 "안 한 것 / 다음 창이 할 것" 절 원문 그대로
  4) 2_KM도구에서 번호가 가장 큰 사용법_vN.txt 파일명
  5) km_tools 안 t*.py 중 가장 큰 번호 (다음 새 도구가 몇 번부터인지)

새 창이 할 일 (CLAUDE.md 1절에 이 순서로 박아 둔다) :
  세션 시작 → 이 스크립트 실행 → 출력 그대로(요약하지 말고) 차장님께 보여주고 →
  「무엇부터 할까요?」 한 줄만. 이 출력과 차장님이 알고 있는 상태가 다르면
  그 자리에서 바로 어긋난 것을 알 수 있다 — 여러 턴을 쓴 뒤에 발견하지 않는다.
"""
from __future__ import print_function
import os, re, subprocess, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))          # .../배포4/3_공통사용/인수인계함
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))  # 저장소 루트
TOOLS = os.path.join(REPO, '배포4', '2_KM도구', '코드', 'km_tools')
USAGE_DIR = os.path.join(REPO, '배포4', '2_KM도구')

VERSION = 'v1 2026-09-28'


def _run(cmd):
    try:
        return subprocess.check_output(cmd, cwd=REPO, stderr=subprocess.STDOUT).decode('utf-8', 'replace').strip()
    except Exception as e:
        return '(git 실패 : %s)' % e


def _latest_numbered(pattern, group=1):
    """pattern 에 맞는 파일 중 vN 번호가 가장 큰 것 하나. (경로, N) 또는 (None, 0)"""
    best_path, best_n = None, -1
    for p in glob.glob(pattern):
        m = re.search(r'_v(\d+)', os.path.basename(p))
        if not m:
            continue
        n = int(m.group(1))
        if n > best_n:
            best_n, best_path = n, p
    return best_path, best_n


def _section(md_text, *headers):
    """마크다운에서 헤더(## 로 시작) 중 이름이 headers 중 하나를 담은 절 원문."""
    lines = md_text.splitlines()
    out, on = [], False
    for ln in lines:
        if ln.startswith('#'):
            on = any(h in ln for h in headers)
            if on:
                out.append(ln)
            continue
        if on:
            out.append(ln)
    return '\n'.join(out).strip()


def run():
    L = []
    L.append('=' * 60)
    L.append('새창 자가진단 (%s) — 새 창이 첫 답변 전에 돌린 것' % VERSION)
    L.append('=' * 60)

    L.append('')
    L.append('[1] 브랜치·최신 커밋 3개')
    L.append('브랜치 : ' + _run(['git', 'branch', '--show-current']))
    L.append(_run(['git', 'log', '--oneline', '-3']))

    L.append('')
    L.append('[2] 가장 최신 인수인계 파일')
    hpath, hn = _latest_numbered(os.path.join(HERE, '2_창이어가기_v*.md'))
    if hpath:
        L.append(os.path.basename(hpath))
        with open(hpath, 'r', encoding='utf-8') as f:
            htext = f.read()
        L.append('')
        L.append('[3] 그 파일의 "안 한 것 / 다음 창이 할 것" 절 (원문)')
        sec = _section(htext, '안 한 것', '다음 창이 할 것', '다음 창', '결정대기')
        L.append(sec if sec else '(그런 이름의 절을 못 찾음 — 파일을 직접 열어 확인)')
    else:
        L.append('(인수인계함에 2_창이어가기_vN_*.md 가 없음)')

    L.append('')
    L.append('[4] 가장 최신 사용법 파일')
    upath, un = _latest_numbered(os.path.join(USAGE_DIR, '사용법_v*.txt'))
    L.append(os.path.basename(upath) if upath else '(없음)')

    L.append('')
    L.append('[5] km_tools 안 t*.py 중 가장 큰 번호 (다음 새 도구 번호 참고용)')
    best_t, best_tn = None, -1
    if os.path.isdir(TOOLS):
        for fn in os.listdir(TOOLS):
            m = re.match(r'^t(\d+)_', fn)
            if m and int(m.group(1)) > best_tn:
                best_tn, best_t = int(m.group(1)), fn
    L.append('%s (t%d 번)' % (best_t, best_tn) if best_t else '(못 찾음)')

    L.append('')
    L.append('=' * 60)
    return '\n'.join(L)


if __name__ == '__main__':
    print(run())
    sys.exit(0)
