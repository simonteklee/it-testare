' IT-testare - startar servern i bakgrunden (dolt) och oppnar i app-lage (eget fonster).
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
dir = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = dir
sh.Run """" & dir & "\.venv\Scripts\uvicorn.exe"" app.main:app --host 127.0.0.1 --port 8765", 0, False
WScript.Sleep 3000
url = "http://127.0.0.1:8765"
edge1 = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
edge2 = "C:\Program Files\Microsoft\Edge\Application\msedge.exe"
chrome = sh.ExpandEnvironmentStrings("%ProgramFiles%") & "\Google\Chrome\Application\chrome.exe"
If fso.FileExists(edge1) Then
  sh.Run """" & edge1 & """ --app=" & url, 1, False
ElseIf fso.FileExists(edge2) Then
  sh.Run """" & edge2 & """ --app=" & url, 1, False
ElseIf fso.FileExists(chrome) Then
  sh.Run """" & chrome & """ --app=" & url, 1, False
Else
  sh.Run url, 1, False
End If
