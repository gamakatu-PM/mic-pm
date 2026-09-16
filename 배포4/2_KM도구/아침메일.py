# -*- coding: utf-8 -*-
"""KM 아침 메일 - 작업 스케줄러가 05:00 에 부르는 파일. 직접 눌러도 됩니다."""
import os, sys, runpy
HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(HERE, '코드', 'km_tools')
sys.path.insert(0, TOOLS)
import common
common.AUTO = True
import t35_morningmail
t35_morningmail.auto()
