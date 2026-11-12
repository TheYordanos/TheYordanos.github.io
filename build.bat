@echo off
rem Builds articles\*.html from content\*.md with Pandoc, then regenerates the
rem article list in index.html using the PowerShell code embedded at the bottom
rem of this file (everything after the #PS-BEGIN line).
rem
rem Front matter per article:
rem   ---
rem   title: Chess in Odin
rem   description: Short summary for the meta tag.
rem   date: 2026-09-12        (YYYY-MM-DD, newest first)
rem   draft: true             (optional, skips the article)
rem   ---

setlocal
cd /d "%~dp0"

set "CONTENT_DIR=articles\content"
set "OUT_DIR=articles"
set "ARTICLE_TPL=articles\template.txt"
set "INDEX=%~dp0index.html"
set "RC=0"
set "COUNT=0"

rem ---- checks ---------------------------------------------------------------
where pandoc >nul 2>nul
if errorlevel 1 (
	echo error: pandoc not found. Install it, then open a NEW terminal window.
	set "RC=1"
	goto :done
)

if not exist "%ARTICLE_TPL%" (
	echo error: missing %ARTICLE_TPL%
	set "RC=1"
	goto :done
)

if not exist "%INDEX%" (
	echo error: missing index.html
	set "RC=1"
	goto :done
)

findstr /c:"ARTICLES:START" "%INDEX%" >nul || goto :nomarkers
findstr /c:"ARTICLES:END" "%INDEX%" >nul || goto :nomarkers

rem ---- temp files -----------------------------------------------------------
set "WORK=%TEMP%\article-build-%RANDOM%"
mkdir "%WORK%"
set "STATUS_TPL=%WORK%\status.tpl"
set "ITEM_TPL=%WORK%\item.tpl"
set "ITEMS=%WORK%\items.txt"

rem Pandoc templates (written without a trailing newline)
<nul set /p "=$if(draft)$draft$else$ok$endif$" >"%STATUS_TPL%"
<nul set /p "=$date$|$slug$|$title$" >"%ITEM_TPL%"
type nul >"%ITEMS%"

rem ---- clean + build --------------------------------------------------------
if not exist "%OUT_DIR%" mkdir "%OUT_DIR%"
del /q "%OUT_DIR%\*.html" 2>nul

for %%f in ("%CONTENT_DIR%\*.md") do call :build "%%f"
if "%RC%"=="1" goto :done

rem ---- update index.html (embedded PowerShell, reads ITEMS and INDEX) -------
powershell -NoProfile -ExecutionPolicy Bypass -Command "$t = [IO.File]::ReadAllText('%~f0'); & ([scriptblock]::Create($t.Substring($t.LastIndexOf('#PS-BEGIN'))))"
if errorlevel 1 (
	set "RC=1"
	goto :done
)

echo done: %COUNT% article^(s^), index.html updated
goto :done

:nomarkers
echo error: index.html needs these two lines inside the articles list:
echo   ^<!-- ARTICLES:START --^>
echo   ^<!-- ARTICLES:END --^>
set "RC=1"
goto :done

:done
if defined WORK if exist "%WORK%" rmdir /s /q "%WORK%"
rem Keep the window open when launched by double-click
echo %cmdcmdline% | find /i "/c" >nul && pause
exit /b %RC%

rem ---- build one article ----------------------------------------------------
:build
if "%RC%"=="1" exit /b 1
set "SRC=%~1"
set "SLUG=%~n1"

set "STATUS=ok"
for /f "usebackq delims=" %%s in (`pandoc "%SRC%" -t html --template="%STATUS_TPL%"`) do set "STATUS=%%s"
if /i "%STATUS:~0,5%"=="draft" (
	echo skip   %SLUG% [draft]
	exit /b 0
)

pandoc "%SRC%" --from markdown --to html5 --template="%ARTICLE_TPL%" --syntax-highlighting=none -o "%OUT_DIR%\%SLUG%.html"
if errorlevel 1 (
	echo error: pandoc failed on %SRC%
	set "RC=1"
	exit /b 1
)

pandoc "%SRC%" -t html --template="%ITEM_TPL%" -M "slug=%SLUG%" >>"%ITEMS%"
echo.>>"%ITEMS%"

echo built  %OUT_DIR%\%SLUG%.html
set /a COUNT+=1
exit /b 0

#PS-BEGIN
# Embedded PowerShell: sorts articles newest first and replaces everything
# between the ARTICLES markers in index.html. Reads/writes UTF-8 without BOM
# so non-Latin text (e.g. Amharic) is preserved.

$Items = $env:ITEMS
$Index = $env:INDEX

$ErrorActionPreference = 'Stop'
$utf8 = New-Object System.Text.UTF8Encoding($false)
$startMark = '<!-- ARTICLES:START -->'
$endMark = '<!-- ARTICLES:END -->'

try {
    # ---- read items ---------------------------------------------------------
    $rows = @()
    foreach ($line in [IO.File]::ReadAllLines($Items, $utf8)) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }

        $p = $line -split '\|', 3
        if ($p.Count -lt 2) { continue }

        $date = $p[0].Trim()
        $slug = $p[1].Trim()
        $title = ''
        if ($p.Count -gt 2) { $title = $p[2].Trim() }

        if (-not $date) {
            Write-Warning "$slug has no date; it will sort last"
            $date = '0000-00-00'
        }
        if (-not $title) {
            Write-Warning "$slug has no title; using filename"
            $title = $slug
        }

        $rows += [pscustomobject]@{ Date = $date; Slug = $slug; Title = $title }
    }

    # ---- build the list (newest first) --------------------------------------
    $sorted = @($rows | Sort-Object -Property @{ Expression = 'Date'; Descending = $true }, @{ Expression = 'Title'; Descending = $false })
    $lines = @()
    foreach ($r in $sorted) {
        $lines += ("`t`t`t`t" + '<li><a href="articles/' + $r.Slug + '.html">' + $r.Title + '</a></li>')
    }

    # ---- splice into index.html ---------------------------------------------
    $text = [IO.File]::ReadAllText($Index, $utf8)
    $nl = "`n"
    if ($text.Contains("`r`n")) { $nl = "`r`n" }

    $s = $text.IndexOf($startMark, [StringComparison]::Ordinal)
    $e = $text.IndexOf($endMark, [StringComparison]::Ordinal)
    if ($s -lt 0 -or $e -lt 0 -or $e -lt $s) {
        throw "index.html needs $startMark followed by $endMark"
    }

    # keep the END marker's indentation
    $lineStart = $text.LastIndexOf([char]10, $e) + 1
    $indent = ''
    if ($lineStart -gt $s) { $indent = $text.Substring($lineStart, $e - $lineStart) }
    if ($indent.Trim() -ne '') { $indent = '' }

    $head = $text.Substring(0, $s + $startMark.Length)
    $tail = $text.Substring($e)

    $body = ''
    if ($lines.Count -gt 0) { $body = ($lines -join $nl) + $nl }

    $new = $head + $nl + $body + $indent + $tail
    [IO.File]::WriteAllText($Index, $new, $utf8)

    Write-Host "index.html updated with $($lines.Count) article(s)"
}
catch {
    Write-Host "error: $($_.Exception.Message)"
    exit 1
}
