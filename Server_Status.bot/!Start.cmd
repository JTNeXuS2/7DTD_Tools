@echo off
title "7DTD_bot %cd%"

:start
python 7DTD_bot.py
timeout /t 5
goto start
