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
from anki.utils import isWin, isMac
from aqt.addcards import AddCards
from aqt.browser import Browser
from switcher.listloc import localIdent2Name
if isWin:
    import win32api
# the Anki alpha builds for windows come without isLin defined
isLin = not isWin and not isMac

startLayout = 'us'
loadedLayouts = []
availableLayouts = [] 

# isLin is undefined in the Windows alpha build ???
isLin = not isWin and not isMac

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
        win32api.LoadKeyboardLayout(localIdent2Name[mw.col.decks.confForDid(mw.col.decks.current()['id']).get('questionLayout', startLayout)],1)
    elif num == 1:
        win32api.LoadKeyboardLayout(localIdent2Name[mw.col.decks.confForDid(mw.col.decks.current()['id']).get('answerLayout', startLayout)],1)

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

def restoreOrigLayout(self=None):
    if isLin:
        subprocess.run(["setxkbmap", startLayout])
    elif isWin:
        win32api.LoadKeyboardLayout(startLayout,1)

def onEditFocusLost(b, note, currentField):
    restoreOrigLayout()

# linux only (fixme?)
if isLin: 
    getCurrentLayout()
    #populate list with available layouts
    getLayouts()
    addHook("editFocusGained", onFocusGainedLin)

if isWin:
    getCurrentLayoutWin()
    # populate list with available layouts
    availableLayouts = localIdent2Name.keys()
    addHook("editFocusGained", onFocusGainedWin)

if not isMac:
    Ui_Dialog.setupUi = wrap(Ui_Dialog.setupUi, newSetupUi)
    DeckConf.loadConf = wrap(DeckConf.loadConf, nLoadConf)
    DeckConf.saveConf = wrap(DeckConf.saveConf, nSaveConf)
    addHook("editFocusLost", onEditFocusLost)
    # Hacks at different points to restore the original layout after closing the browser/editor/anki
    AnkiQt.closeEvent = wrap(AnkiQt.closeEvent, nCloseEvent, "before")
    AddCards.reject = wrap(AddCards.reject, restoreOrigLayout)
    Browser.closeEvent = wrap(Browser.closeEvent, nCloseEvent, "before")
