@echo off
rem set logdir="H:\Projects\UKPlanning\dbs"
rem set dbdir="H:\Projects\UKPlanning\logs"
set test="H:\Projects\UKPlanning\ukplanning\test.py"
rem python %run% %* -g %logdir% -d %dbdir%
IF "%1"=="" GOTO :NOARGS
IF "%2"=="" GOTO :ONEARG
GOTO :MANYARGS
:NOARGS
python %test% -h
GOTO :EOF
:ONEARG
python %test% -s %1 -g "working"
GOTO :EOF
:MANYARGS
python %test% %*
:EOF
pause

