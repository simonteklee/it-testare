' IT-testare - startar servern i bakgrunden (dolt) och öppnar webbläsaren.
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
dir = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = dir
sh.Run """" & dir & "\.venv\Scripts\uvicorn.exe"" app.main:app --host 127.0.0.1 --port 8765", 0, False
WScript.Sleep 3000
sh.Run "http://127.0.0.1:8765", 1, False
