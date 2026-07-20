@echo off
REM ============================================================================
REM  Executar download e conversao RAIS -> CSV
REM  Usa R.exe (NAO Rscript.exe) devido a bug de segfault no Rscript do sistema
REM ============================================================================

echo ========================================
echo   DOWNLOAD RAIS - CONVERSAO PARA CSV
echo ========================================
echo.

set R_EXE=C:\Program Files\R\R-4.6.0\bin\R.exe
set R_SCRIPT=C:\Users\oorie\OneDrive\Documentos\TRABALHOS\SAUDE DO TRABALHADOR\scripts\download_rais_csv.R
set R_LOG=C:\Users\oorie\OneDrive\Documentos\TRABALHOS\SAUDE DO TRABALHADOR\scripts\download_rais_csv.log

echo Inicio: %date% %time%
echo Script: %R_SCRIPT%
echo Log: %R_LOG%
echo.

"%R_EXE%" --no-init-file --no-restore --no-save -f "%R_SCRIPT%" > "%R_LOG%" 2>&1

echo.
echo ========================================
echo   CONCLUIDO (codigo de saida: %ERRORLEVEL%)
echo ========================================
echo.
echo Log salvo em: %R_LOG%
echo.

type "%R_LOG%"

pause
