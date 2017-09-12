REM @echo off

rem C:\Python27\Lib\site-packages\PySide\pyside-rcc.exe -o resources_rc.py resources.qrc
C:\Python27\Lib\site-packages\PySide\pyside-rcc.exe -o pysrb4w_rc.py pysrb4w.qrc
for %%i in (*.ui) do pyside-uic %%i > %%~ni_ui.py

REM pause