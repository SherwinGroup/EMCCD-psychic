@ECHO OFF
set input="%~1"
set postpend="_ui.py"
set output=%input:~1,-4%
"C:\Program Files\WinPython\python-2.7.6.amd64\Lib\site-packages\PyQt4\pyrcc4.exe" -o %input:~0,-5%_rc.py" %input%