# -*- coding: utf-8 -*-
'''
    Copyright (C) 2016 Julian Dehm

    This file is part of "anki layout switcher".

    "anki layout switcher" is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    "anki layout switcher" is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with "anki layout switcher".  If not, see <http://www.gnu.org/licenses/>.
'''


from anki.hooks import addHook, wrap
import re
import subprocess
from anki.decks import defaultConf
from aqt import mw
from aqt.main import AnkiQt
import aqt
from aqt.forms.dconf import Ui_Dialog
from aqt.qt import *
from PyQt5 import QtCore, QtGui, QtWidgets
from aqt.deckconf import DeckConf
from anki.utils import *
from aqt.addcards import AddCards
from aqt.browser import Browser

startLayout = 'us'
loadedLayouts = []
availableLayouts = [] 

class LayoutDetectionError(Exception):
    def __init__(self):
        Exception.__init__(self, "Couldn't detect the current keyboard layout")

class NoLayoutsFound(Exception):
    def __init__(self):
        Exception.__init__(self, "Unable to detect available layouts")


# switch layout according to the field in focus for Linux
def onFocusGainedLin(note, num):
    if num == 0:
        subprocess.run(["setxkbmap",mw.col.decks.confForDid(mw.col.decks.current()['id']).get('questionLayout', startLayout)])
    elif num == 1:
        subprocess.run(["setxkbmap",mw.col.decks.confForDid(mw.col.decks.current()['id']).get('answerLayout', startLayout)])

# switch layout according to the field in focus for Windows
def onFocusGainedWin(note, num):
    if num == 0:
        win32api.LoadKeyboardLayout(mw.col.decks.confForDid(mw.col.decks.current()['id']).get('questionLayout', startLayout),1)
    elif num == 1:
        win32api.LoadKeyboardLayout(mw.col.decks.confForDid(mw.col.decks.current()['id']).get('answerLayout', startLayout),1)

# read the users current keyboard layout. Only reads the language, variants and other settings are ignored (fixme?)
def getCurrentLayout():
    s = subprocess.Popen(("setxkbmap", "-print"),stdout=subprocess.PIPE).stdout.read()
    reg =re.compile('xkb_symbols   { include \"(\S+)\+(?P<layout>\S+)\+(\S+)')
    res = reg.search(str(s))
    global startLayout 
    startLayout = res.group('layout')
    if not startLayout:
        raise LayoutDetectionError()
        # exit here?

def getCurrentLayoutWin():
    global startLayout, loadedLayouts
    startLayout = win32api.GetKeyboardLayoutName()
    loadedLayouts = win32api.GetKeyboardLayoutList()
    
# hook SetupUi() to add menu option to deck configuration
def newSetupUi(self, Dialog):
     self.gridLayout_4 = QtWidgets.QGridLayout()
     self.gridLayout_4.setObjectName("gridLayout_4")
     self.layout_switch = QtWidgets.QCheckBox(self.tab_5)
     self.layout_switch.setObjectName("layout_switch")
     self.gridLayout_4.addWidget(self.layout_switch, 0, 0, 1, 1)
     self.a_layout_b = QtWidgets.QComboBox(self.tab_5)
     self.a_layout_b.setObjectName("a_layout_b")
     self.gridLayout_4.addWidget(self.a_layout_b, 1, 2, 1, 1)
     self.q_layout_box = QtWidgets.QComboBox(self.tab_5)
     self.q_layout_box.setObjectName("q_layout_box")
     self.gridLayout_4.addWidget(self.q_layout_box, 1, 1, 1, 1)
     self.label_15 = QtWidgets.QLabel(self.tab_5)
     self.label_15.setObjectName("label_15")
     self.gridLayout_4.addWidget(self.label_15, 0, 1, 1, 1)
     self.label_16 = QtWidgets.QLabel(self.tab_5)
     self.label_16.setObjectName("label_16")
     self.gridLayout_4.addWidget(self.label_16, 0, 2, 1, 1)
     self.verticalLayout_6.addLayout(self.gridLayout_4)
     self.tabWidget.setCurrentIndex(3)
     self.layout_switch.setText(_("Autoswitch keyboard layout:"))
     self.label_15.setText(_("Question layout"))
     self.label_16.setText(_("Answer layout"))
     self.a_layout_b.addItems(availableLayouts)
     self.q_layout_box.addItems(availableLayouts)

# hook saveConf() to save our settings
def nSaveConf(self):
    c = self.conf
    f = self.form
    c['autoswitchLayout'] = f.layout_switch.isChecked()
    c['questionLayout'] = f.q_layout_box.currentText()
    c['answerLayout'] = f.a_layout_b.currentText()

# hook loadConf() to load our settings
def nLoadConf(self):
    f = self.form
    self.conf = self.mw.col.decks.confForDid(self.deck['id'])
    c = self.conf
    f.layout_switch.setChecked(c.get('autoswitchLayout',False)) 
    f.q_layout_box.setCurrentIndex(f.q_layout_box.findText(c.get('questionLayout', startLayout)))
    f.a_layout_b.setCurrentIndex(f.q_layout_box.findText(c.get('answerLayout',startLayout)))

# try to find all available layouts on this os
def getLayouts():
    import lxml.etree
    repository = "/usr/share/X11/xkb/rules/base.xml"
    tree = lxml.etree.parse(open(repository))
    layouts = tree.xpath("//layout")
    global availableLayouts
    availableLayouts = list(map(lambda x:x.xpath("./configItem/name")[0].text, layouts))
    if len(availableLayouts) == 0:
        raise NoLayoutsFound()

# hook closeEvent() to change back to the initial layout
def nCloseEvent(self, event):
       restoreOrigLayout(self)

def restoreOrigLayout(self):
    if isLin:
        subprocess.run(["setxkbmap", startLayout])
    elif isWin:
        currentLayoutList = win32api.GetKeyboardLayoutList()
        for layout in currentLayoutList:
            if layout not in loadedLayouts:
                win32api.UnloadKeyboardLayout(layout)
        win32api.LoadKeyboardLayout(startLayout,1)

# linux only (fixme?)
if isLin: 
    getCurrentLayout()
    #populate list with available layouts
    getLayouts()
    addHook("editFocusGained", onFocusGainedLin)

if isWin:
    import win32api
    getCurrentLayoutWin()
    # populate list with available layouts
    availableLayouts = localIdent2Name.keys()
    addHook("editFocusGained", onFocusGainedWin)

if not isMac:
    Ui_Dialog.setupUi = wrap(Ui_Dialog.setupUi, newSetupUi)
    DeckConf.loadConf = wrap(DeckConf.loadConf, nLoadConf)
    DeckConf.saveConf = wrap(DeckConf.saveConf, nSaveConf)
    # Hacks at different points to restore the original layout after editFocus was lost
    AnkiQt.closeEvent = wrap(AnkiQt.closeEvent, nCloseEvent, "before")
    AddCards.reject = wrap(AddCards.reject, restoreOrigLayout)
    Browser.closeEvent = wrap(Browser.closeEvent, nCloseEvent, "before")

localIdent2Name = {
"af-ZA" : "0x00000436",
"sq-AL" : "0x0000041C",
"ar-DZ" : "0x00001401",
"ar-BH" : "0x00003C01",
"ar-EG" : "0x00000C01",
"ar-IQ" : "0x00000801",
"ar-JO" : "0x00002C01",
"ar-KW" : "0x00003401",
"ar-LB" : "0x00003001",
"ar-LY" : "0x00001001",
"ar-MA" : "0x00001801",
"ar-OM" : "0x00002001",
"ar-QA" : "0x00004001",
"ar-SA" : "0x00000401",
"ar-SY" : "0x00002801",
"ar-TN" : "0x00001C01",
"ar-AE" : "0x00003801",
"ar-YE" : "0x00002401",
"hy-AM" : "0x0000042B",
"Cy-az-AZ" : "0x0000082C",
"Lt-az-AZ" : "0x0000042C",
"eu-ES" : "0x0000042D",
"be-BY" : "0x00000423",
"bg-BG" : "0x00000402",
"ca-ES" : "0x00000403",
"zh-CN" : "0x00000804",
"zh-HK" : "0x00000C04",
"zh-MO" : "0x00001404",
"zh-SG" : "0x00001004",
"zh-TW" : "0x00000404",
"zh-CHS" : "0x00000004",
"zh-CHT" : "0x00007C04",
"hr-HR" : "0x0000041A",
"cs-CZ" : "0x00000405",
"da-DK" : "0x00000406",
"div-MV" : "0x00000465",
"nl-BE" : "0x00000813",
"nl-NL" : "0x00000413",
"en-AU" : "0x00000C09",
"en-BZ" : "0x00002809",
"en-CA" : "0x00001009",
"en-CB" : "0x00002409",
"en-IE" : "0x00001809",
"en-JM" : "0x00002009",
"en-NZ" : "0x00001409",
"en-PH" : "0x00003409",
"en-ZA" : "0x00001C09",
"en-TT" : "0x00002C09",
"en-GB" : "0x00000809",
"en-US" : "0x00000409",
"en-ZW" : "0x00003009",
"et-EE" : "0x00000425",
"fo-FO" : "0x00000438",
"fa-IR" : "0x00000429",
"fi-FI" : "0x0000040B",
"fr-BE" : "0x0000080C",
"fr-CA" : "0x00000C0C",
"fr-FR" : "0x0000040C",
"fr-LU" : "0x0000140C",
"fr-MC" : "0x0000180C",
"fr-CH" : "0x0000100C",
"gl-ES" : "0x00000456",
"ka-GE" : "0x00000437",
"de-AT" : "0x00000C07",
"de-DE" : "0x00000407",
"de-LI" : "0x00001407",
"de-LU" : "0x00001007",
"de-CH" : "0x00000807",
"el-GR" : "0x00000408",
"gu-IN" : "0x00000447",
"he-IL" : "0x0000040D",
"hi-IN" : "0x00000439",
"hu-HU" : "0x0000040E",
"is-IS" : "0x0000040F",
"id-ID" : "0x00000421",
"it-IT" : "0x00000410",
"it-CH" : "0x00000810",
"ja-JP" : "0x00000411",
"kn-IN" : "0x0000044B",
"kk-KZ" : "0x0000043F",
"kok-IN" : "0x00000457",
"ko-KR" : "0x00000412",
"ky-KZ" : "0x00000440",
"lv-LV" : "0x00000426",
"lt-LT" : "0x00000427",
"mk-MK" : "0x0000042F",
"ms-BN" : "0x0000083E",
"ms-MY" : "0x0000043E",
"mr-IN" : "0x0000044E",
"mn-MN" : "0x00000450",
"nb-NO" : "0x00000414",
"nn-NO" : "0x00000814",
"pl-PL" : "0x00000415",
"pt-BR" : "0x00000416",
"pt-PT" : "0x00000816",
"pa-IN" : "0x00000446",
"ro-RO" : "0x00000418",
"ru-RU" : "0x00000419",
"sa-IN" : "0x0000044F",
"Cy-sr-SP" : "0x00000C1A",
"Lt-sr-SP" : "0x0000081A",
"sk-SK" : "0x0000041B",
"sl-SI" : "0x00000424",
"es-AR" : "0x00002C0A",
"es-BO" : "0x0000400A",
"es-CL" : "0x0000340A",
"es-CO" : "0x0000240A",
"es-CR" : "0x0000140A",
"es-DO" : "0x00001C0A",
"es-EC" : "0x0000300A",
"es-SV" : "0x0000440A",
"es-GT" : "0x0000100A",
"es-HN" : "0x0000480A",
"es-MX" : "0x0000080A",
"es-NI" : "0x00004C0A",
"es-PA" : "0x0000180A",
"es-PY" : "0x00003C0A",
"es-PE" : "0x0000280A",
"es-PR" : "0x0000500A",
"es-ES" : "0x00000C0A",
"es-UY" : "0x0000380A",
"es-VE" : "0x0000200A",
"sw-KE" : "0x00000441",
"sv-FI" : "0x0000081D",
"sv-SE" : "0x0000041D",
"syr-SY" : "0x0000045A",
"ta-IN" : "0x00000449",
"tt-RU" : "0x00000444",
"te-IN" : "0x0000044A",
"th-TH" : "0x0000041E",
"tr-TR" : "0x0000041F",
"uk-UA" : "0x00000422",
"ur-PK" : "0x00000420",
"Cy-uz-UZ" : "0x00000843",
"Lt-uz-UZ" : "0x00000443",
"vi-VN" : "0x0000042A"}
