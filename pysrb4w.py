# encoding: utf-8
#!/usr/bin/python
import io
import json
import os
import sys
import argparse
import logging
import logging.handlers
import webbrowser
from PySide import QtCore, QtGui
from login import Login
import pysrb4w_ui


try:
    to_unicode = unicode
except NameError:
    to_unicode = str


LOG_LEVELS = {
    'D': logging.DEBUG,
    'I': logging.INFO,
    'W': logging.WARNING,
    'E': logging.CRITICAL
}


class Main(QtGui.QMainWindow, pysrb4w_ui.Ui_MainWindow):

    def __init__(self, loglev):
        QtGui.QMainWindow.__init__(self, None)
        self.setupUi(self)
        # log
        self.log = logging.getLogger('pySRB4W')
        self.log.setLevel(loglev)
        fmt = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        rfh = logging.handlers.RotatingFileHandler('pysrb4w.log', maxBytes=5*1024*1024, backupCount=2)
        rfh.setLevel(self.log.level)
        rfh.setFormatter(fmt)
        self.log.addHandler(rfh)
        con = logging.StreamHandler()
        con.setLevel(self.log.level)
        con.setFormatter(fmt)
        self.log.addHandler(con)
        # cfg
        self.cfgfile = os.path.join(os.path.expanduser('~'), '.pysrb4w.json')
        try:
            with io.open(self.cfgfile) as data_file:
                self.settings = json.load(data_file)
        except Exception as err:
            self.log.warning(err.__str__())
            self.settings = json.loads('{ "x":100, "y":100, "w":700, "h":800 }')
        subs = self.settings.get('subs', [])
        for s in subs:
            self.cmbSubs.addItem(s)
        # init
        self.reddit = None
        self.subreddit = None
        self.lastPost = None
        self.fontsize = 9
        self.cmbSubs.currentIndexChanged.connect(self.onChangeSub)
        self.cmbSubs.editTextChanged.connect(self.onChangeSub)
        self.cmbSort.currentIndexChanged.connect(self.onChangeSub)
        self.btnLoad.clicked.connect(self.onLoadClick)
        self.btnFontInc.clicked.connect(self.onFontIncClick)
        self.btnFontDec.clicked.connect(self.onFontDecClick)
        self.btnLink.clicked.connect(self.onLinkClick)
        self.btnVoteUp.clicked.connect(self.onVoteUpClick)
        self.btnVoteDn.clicked.connect(self.onVoteDnClick)
        self.btnSaved.clicked.connect(self.onSavedClick)
        self.btnHide.clicked.connect(self.onHideClick)

    def closeEvent(self, event):
        event.accept()
        self.settings['maximized'] = self.isMaximized()
        self.settings['x'] = self.pos().x()
        self.settings['y'] = self.pos().y()
        self.settings['w'] = self.size().width()
        self.settings['h'] = self.size().height()
        self.settings['fonts'] = self.fontsize
        subs = []
        if self.cmbSubs.count() > 0:
            for i in range(0, self.cmbSubs.count()):
                subs.append(self.cmbSubs.itemText(i))
        self.settings['subs'] = subs
        str_ = json.dumps(self.settings, indent=4, separators=(',', ':'), ensure_ascii=False)
        with io.open(self.cfgfile, 'w', encoding='utf8') as outfile:
            outfile.write(to_unicode(str_))

    def showEvent(self, event):
        event.accept()
        if self.settings.get('maximized', False):
            self.setWindowState(QtCore.Qt.WindowMaximized)
        else:
            self.resize(self.settings['w'], self.settings['h'])
            self.move(self.settings['x'], self.settings['y'])
        self.fontsize = self.settings.get('fonts', 9)
        self.txtBody.setFont(QtGui.QFont('Calibri', self.fontsize))
        self.login()

    def onChangeSub(self):
        self.subreddit = None

    def onLoadClick(self):
        if self.cmbSubs.currentText() == '':
            return
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            if not self.subreddit:
                sub = self.cmbSubs.currentText().lower()
                if self.cmbSort.currentIndex() == 0:
                    self.subreddit = self.reddit.subreddit(sub).top('all', limit=50)
                elif self.cmbSort.currentIndex() == 1:
                    self.subreddit = self.reddit.subreddit(sub).hot(limit=50)
                else:
                    self.subreddit = self.reddit.subreddit(sub).new(limit=50)
                if self.cmbSubs.findText(sub) < 0:
                    self.cmbSubs.addItem(sub)
            #
            self.lastPost = self.subreddit.next()
            self.btnVoteUp.setChecked(self.lastPost.likes is True)
            self.btnVoteDn.setChecked(self.lastPost.likes is False)
            self.btnSaved.setChecked(self.lastPost.saved)
            self.txtBody.setHtml('<p><b>%s</b></p>%s' % (self.lastPost.title, self.lastPost.selftext_html))
            self.txtBody.setFocus()
            QtGui.QApplication.restoreOverrideCursor()
        except Exception as err:
            QtGui.QApplication.restoreOverrideCursor()
            self.subreddit = None
            self.log.error(err.__str__())
            QtGui.QMessageBox.critical(self, 'Subreddit error', err.__str__())

    def onFontIncClick(self):
        self.fontsize += 1
        self.txtBody.setFont(QtGui.QFont('Calibri', self.fontsize))

    def onFontDecClick(self):
        self.fontsize -= 1
        self.txtBody.setFont(QtGui.QFont('Calibri', self.fontsize))

    def onLinkClick(self):
        if self.lastPost:
            webbrowser.open('www.reddit.com' + self.lastPost.permalink)

    def onVoteUpClick(self):
        if not self.lastPost:
            return
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            if self.lastPost.likes is True:
                self.lastPost.clear_vote()
                self.lastPost.likes = None
            else:
                self.lastPost.upvote()
                self.lastPost.likes = True
            self.btnVoteUp.setChecked(self.lastPost.likes is True)
            self.btnVoteDn.setChecked(self.lastPost.likes is False)
            QtGui.QApplication.restoreOverrideCursor()
        except Exception as err:
            QtGui.QApplication.restoreOverrideCursor()
            self.log.error(err.__str__())
            QtGui.QMessageBox.critical(self, 'Subreddit error', err.__str__())

    def onVoteDnClick(self):
        if not self.lastPost:
            return
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            if self.lastPost.likes is False:
                self.lastPost.clear_vote()
                self.lastPost.likes = None
            else:
                self.lastPost.downvote()
                self.lastPost.likes = False
            self.btnVoteUp.setChecked(self.lastPost.likes is True)
            self.btnVoteDn.setChecked(self.lastPost.likes is False)
            QtGui.QApplication.restoreOverrideCursor()
        except Exception as err:
            QtGui.QApplication.restoreOverrideCursor()
            self.log.error(err.__str__())
            QtGui.QMessageBox.critical(self, 'Subreddit error', err.__str__())

    def onSavedClick(self):
        if not self.lastPost:
            return
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            if self.lastPost.saved:
                self.lastPost.unsave()
                self.lastPost.saved = False
            else:
                self.lastPost.save()
                self.lastPost.saved = True
            self.btnSaved.setChecked(self.lastPost.saved)
            QtGui.QApplication.restoreOverrideCursor()
        except Exception as err:
            QtGui.QApplication.restoreOverrideCursor()
            self.log.error(err.__str__())
            QtGui.QMessageBox.critical(self, 'Subreddit error', err.__str__())

    def onHideClick(self):
        if not self.lastPost:
            return
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            self.lastPost.hide()
            QtGui.QApplication.restoreOverrideCursor()
        except Exception as err:
            QtGui.QApplication.restoreOverrideCursor()
            self.log.error(err.__str__())
            QtGui.QMessageBox.critical(self, 'Subreddit error', err.__str__())
            return
        self.onLoadClick()

    def login(self):
        dlg = Login(self)
        if dlg.exec_() == QtGui.QDialog.Accepted:
            self.reddit = dlg.reddit
            self.setWindowTitle('SRB4W [%s]' % self.reddit.user.me())
            self.onLoadClick()
        else:
            sys.exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='pySRB4W')
    parser.add_argument('-l', '--log', choices=LOG_LEVELS, default='I', help='Messaggi da mostrare: D=debug, I=info, W=warning, E=errori (default "I")')
    args = parser.parse_args()
    app = QtGui.QApplication(sys.argv)
    w = Main(LOG_LEVELS[args.log])
    w.show()
    sys.exit(app.exec_())
