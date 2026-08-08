@echo off
setlocal enabledelayedexpansion
title ORTHO4XP V3 - Installation Windows

:: ============================================================
::  ORTHO4XP - Lanceur d'installation Windows
::  Double-cliquez sur ce fichier pour demarrer.
:: ============================================================

:: Se placer dans le dossier de ce lanceur
cd /d "%~dp0"

echo ============================================================
echo   ORTHO4XP - Installation Windows
echo ============================================================
echo.

:: 1) Verifier la presence du script d'installation
if not exist "INSTALL_PREREQUIS.py" (
    echo [ERREUR] Fichier INSTALL_PREREQUIS.py introuvable.
    echo Placez ce lanceur dans le meme dossier que INSTALL_PREREQUIS.py.
    echo.
    pause
    exit /b 1
)

:: 2) Rechercher un interpreteur Python valide
::    Priorite au lanceur officiel "py" : il ignore le faux python du Store.
set "PYEXE="

where py >nul 2>&1
if !errorlevel! equ 0 (
    for %%V in (3.12 3.11 3) do (
        if not defined PYEXE (
            py -%%V -c "import sys" >nul 2>&1
            if !errorlevel! equ 0 set "PYEXE=py -%%V"
        )
    )
)

:: Repli sur "python" du PATH si "py" est absent.
:: Le faux python du Microsoft Store echoue a ce test et n'est donc pas retenu.
if not defined PYEXE (
    where python >nul 2>&1
    if !errorlevel! equ 0 (
        python -c "import sys" >nul 2>&1
        if !errorlevel! equ 0 set "PYEXE=python"
    )
)

:: 3) Aucun Python valide trouve -> guider l'utilisateur
if not defined PYEXE (
    echo [ERREUR] Aucun vrai Python n'a ete trouve sur cet ordinateur.
    echo.
    echo Windows affiche peut-etre un faux "python" du Microsoft Store
    echo qui ne fonctionne pas reellement. Il faut installer le vrai Python.
    echo.
    echo La page de telechargement officielle va s'ouvrir dans votre navigateur.
    echo   1. Telechargez et installez Python 3.12
    echo   2. COCHEZ la case "Add Python to PATH" pendant l'installation
    echo   3. Relancez ensuite ce fichier
    echo.
    start "" "https://www.python.org/downloads/"
    echo.
    pause
    exit /b 1
)

echo Python detecte : !PYEXE!
echo Lancement de l'installation...
echo.

:: 4) Lancer le script d'installation
!PYEXE! INSTALL_PREREQUIS.py
set "RC=!errorlevel!"

echo.
if "!RC!"=="0" (
    echo Installation terminee.
) else (
    echo [ERREUR] L'installation s'est interrompue. Code : !RC!
    echo Lisez les messages ci-dessus pour identifier la cause.
)
echo.
echo Appuyez sur une touche pour fermer cette fenetre...
pause >nul
endlocal
