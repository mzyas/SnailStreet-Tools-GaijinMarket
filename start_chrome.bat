@echo off
setlocal enabledelayedexpansion

:: 1. 获取项目根目录（即当前 bat 脚本所在的文件夹）
set "PROJECT_ROOT=%~dp0"
:: 去掉末尾的斜杠
set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"

:: 2. 定义用户数据文件夹路径
set "USER_DATA_DIR=%PROJECT_ROOT%\ChromeGaijinMarketData"

:: 3. 如果文件夹不存在则创建
if not exist "%USER_DATA_DIR%" (
    echo Creating folder: %USER_DATA_DIR%
    mkdir "%USER_DATA_DIR%"
)

:: 4. 自动寻找本机 Chrome 的路径
:: 尝试从注册表获取标准安装路径
set "CHROME_PATH="
for /f "tokens=2*" %%a in ('reg query "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe" /ve 2^>nul') do set "CHROME_PATH=%%b"

:: 如果注册表没找到，尝试默认路径
if "%CHROME_PATH%"=="" (
    if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
        set "CHROME_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe"
    ) else if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
        set "CHROME_PATH=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    )
)

:: 5. 启动 Chrome
if defined CHROME_PATH (
    echo Starting Chrome from: %CHROME_PATH%
    start "" "%CHROME_PATH%" --remote-debugging-port=9222 --user-data-dir="%USER_DATA_DIR%"
) else (
    echo [Error] Could not find Chrome. Please check if it is installed.
    pause
)

endlocal