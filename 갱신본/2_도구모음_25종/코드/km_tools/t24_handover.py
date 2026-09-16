# -*- coding: utf-8 -*-
"""24. 인수인계함 열기 - 클로드가 여쭌 것(결정 대기)을 보여주고 폴더를 연다.
컴퓨터 앞에 계실 때 이것만 누르면 흘러간 질문이 다시 눈에 들어옵니다."""
import os, glob
from common import *

def latest_xlsx(root):
    c = sorted(glob.glob(os.path.join(root, '*결정대기*.xlsx')),
               key=lambda p: os.path.getmtime(p), reverse=True)
    return c[0] if c else None

def run():
    title('24. 인수인계함 (클로드가 여쭌 것)')
    root = cfg('handover')
    if not os.path.isdir(root):
        print('[없음] %s' % root)
        print('  -> KM_인수인계함 폴더를 그 자리에 두시거나, 설정.ini 의 handover 경로를 고쳐주십시오.')
        return
    x = latest_xlsx(root)
    if not x:
        print('결정대기 엑셀이 없습니다. 폴더만 엽니다.')
    else:
        print('최신 파일 : %s' % os.path.basename(x))
        try:
            import openpyxl
            ws = openpyxl.load_workbook(x, data_only=True)['결정대기']
            rows = []
            for r in ws.iter_rows(min_row=5, values_only=True):
                if not r or not r[0]:
                    continue
                no, urg, kind, what, why, risk = r[0], r[1], r[2], r[3], r[4], r[5]
                ans = r[8] if len(r) > 8 else ''
                done = r[9] if len(r) > 9 else ''
                if done or (ans and str(ans).strip()):
                    continue
                rows.append((no, urg, kind, what))
            print('')
            print('아직 답 안 하신 것 %s건' % won(len(rows)))
            print('%-4s %-7s %-6s %s' % ('번호', '급함', '구분', '무엇을'))
            print('-' * 78)
            for no, urg, kind, what in sorted(rows, key=lambda x: (x[1] != '★급함', x[0])):
                print('%-4s %-7s %-6s %s' % (no, urg, kind, str(what)[:52]))
        except ImportError:
            print('openpyxl 이 없어 내용을 못 읽습니다. 폴더만 엽니다.')
        except Exception as e:
            print('[읽기 실패] %s' % e)
    print('')
    print('폴더를 엽니다 : %s' % root)
    print('(0_지금_봐야_할_것.html 을 더블클릭하시면 링크가 다 걸려 있습니다)')
    open_folder(root)
    log('인수인계함', os.path.basename(x) if x else '엑셀없음')

if __name__ == '__main__':
    run(); pause()
