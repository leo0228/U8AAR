
@set PATH=%~dp0\tool\win;%PATH%
python.exe scripts\pack.py -r -s -t 1 %1 %2 %3 %4
@pause