@echo off
echo Building UniversalDownloader by Morris...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist UniversalDownloader.spec del UniversalDownloader.spec

:: First, attempt to find where customtk is located in this environment
:: Assuming it is in venv/Lib/site-packages/customtkinter or similiar.
:: We will let pyinstaller find imports, but we must be careful about data files.
:: Customtkinter needs its json/theme files.
:: We can use --collect-all customtkinter to be safe.

pyinstaller --noconfirm --onefile --windowed ^
 --name "UniversalDownloader" ^
 --collect-all customtkinter ^
 --add-data "config.py;." ^
 --icon=NONE ^
 GuiPrincipal.py

echo.
echo Build complete. Check the 'dist' folder.
pause
