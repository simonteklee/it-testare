' TestARN - startar servern (dolt, loggar till testarn.log) och oppnar i app-lage.
Set sh  = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
dir = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = dir
q   = Chr(34)
url = "http://127.0.0.1:8765"
log = dir & "\testarn.log"

If Not fso.FileExists(dir & "\.venv\Scripts\uvicorn.exe") Then
  MsgBox "TestARN verkar inte vara installerat (hittar ingen server)." & vbCrLf & _
         "Kor installationsraden i PowerShell forst.", 16, "TestARN"
  WScript.Quit
End If

' Starta servern via hjalpskriptet (loggar till testarn.log)
sh.Run "cmd /c " & q & dir & "\start-server.cmd" & q, 0, False

' Vanta tills servern svarar (max ~30 s)
ready = False
For i = 1 To 30
  WScript.Sleep 1000
  If UrlReady(url & "/api/health") Then
    ready = True
    Exit For
  End If
Next

If Not ready Then
  MsgBox "TestARN-servern startade inte." & vbCrLf & vbCrLf & _
         "Stang inte fonstret - skicka loggfilen till Simon:" & vbCrLf & log, 16, "TestARN - fel"
End If

' Oppna i app-lage om mojligt (annars vanlig webblasare)
edge1  = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
edge2  = "C:\Program Files\Microsoft\Edge\Application\msedge.exe"
chrome = sh.ExpandEnvironmentStrings("%ProgramFiles%") & "\Google\Chrome\Application\chrome.exe"
If fso.FileExists(edge1) Then
  sh.Run q & edge1 & q & " --app=" & url, 1, False
ElseIf fso.FileExists(edge2) Then
  sh.Run q & edge2 & q & " --app=" & url, 1, False
ElseIf fso.FileExists(chrome) Then
  sh.Run q & chrome & q & " --app=" & url, 1, False
Else
  sh.Run url, 1, False
End If

Function UrlReady(u)
  Dim h
  UrlReady = False
  On Error Resume Next
  Set h = CreateObject("MSXML2.ServerXMLHTTP.6.0")
  If Err.Number <> 0 Then
    Err.Clear
    Set h = CreateObject("MSXML2.XMLHTTP")
  End If
  If Err.Number <> 0 Then Exit Function
  h.open "GET", u, False
  h.send
  If Err.Number = 0 And h.status = 200 Then UrlReady = True
  On Error GoTo 0
End Function
