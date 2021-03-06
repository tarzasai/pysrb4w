# encoding: utf-8
import praw
from PySide import QtCore, QtGui
import login_ui


class Login(QtGui.QDialog, login_ui.Ui_Dialog):

    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.reddit = None
        self.settings = parent.settings
        self.btnOk.clicked.connect(self.onOkClick)

    def showEvent(self, event):
        event.accept()
        self.edtCId.setText(self.settings.get('cid', None))
        self.edtCSe.setText(self.settings.get('cse', None))
        self.edtUsr.setText(self.settings.get('usr', None))
        if self.cid == '':
            self.edtCId.setFocus()
        else:
            self.edtPwd.setFocus()

    def onOkClick(self):
        if not (self.cid != '' and self.cse != '' and self.usr != '' and self.pwd != ''):
            return
        self.lblError.setText(None)
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            reddit = praw.Reddit(client_id=self.cid, client_secret=self.cse, password=self.pwd,
                user_agent='pysrb4w by /u/esorciccio', username=self.usr)
            self.settings['cid'] = self.cid
            self.settings['cse'] = self.cse
            self.settings['usr'] = self.usr
            self.reddit = reddit
            if self.reddit.user.me().name != self.usr:
                raise Exception("Username doesn't match!") ##: " + self.reddit.user.me().name)
            self.accept()
        except Exception as err:
            self.lblError.setText(err.__str__())
        finally:
            QtGui.QApplication.restoreOverrideCursor()

    @property
    def cid(self):
        return self.edtCId.text()

    @property
    def cse(self):
        return self.edtCSe.text()

    @property
    def usr(self):
        return self.edtUsr.text()

    @property
    def pwd(self):
        return self.edtPwd.text()
