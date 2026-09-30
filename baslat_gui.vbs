' ------------------------------------------------------------
' Retro+ Download Manager - tamamen gizli baslatici
'
' Hicbir CMD/konsol penceresi acmadan (ne baslarken ne de
' calisirken) arayuzu baslatir. Masaustu kisayolu icin:
'   wscript.exe  "C:\yol\baslat_gui.vbs"
'
' Klasik konsolu gorunur baslatici: baslat_gui.bat
' ------------------------------------------------------------
Option Explicit

Dim shell, fso, here, bat
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

here = fso.GetParentFolderName(WScript.ScriptFullName)
bat = fso.BuildPath(here, "baslat_gui.bat")

If Not fso.FileExists(bat) Then
    MsgBox "baslat_gui.bat bulunamadi:" & vbCrLf & vbCrLf & bat, _
           vbExclamation, "Retro+ Download Manager"
    WScript.Quit 1
End If

' pythonw.exe var mi? (yoksa gizli pencerede hata kaybolur)
If FindPythonw() = "" Then
    MsgBox "pythonw.exe bulunamadi, program baslatilamadi." & vbCrLf & vbCrLf & _
           "Python 3 kurulu degil." & vbCrLf & _
           "Kurulum:  winget install Python.Python.3.13" & vbCrLf & _
           "Elle denemek icin konsolda:" & vbCrLf & _
           "  python -m download_manager", _
           vbCritical, "Retro+ Download Manager"
    WScript.Quit 1
End If

shell.CurrentDirectory = here
' 0 = pencere gizli, False = bekleme (aninda doner)
shell.Run """" & bat & """", 0, False


' PATH, bilinen kurulum klasorleri ve pyw.exe uzerinden arar.
Function FindPythonw()
    Dim dirs, i, cand, folder, base

    On Error Resume Next

    dirs = Split(shell.Environment("PROCESS")("PATH"), ";")
    For i = 0 To UBound(dirs)
        If Len(Trim(dirs(i))) > 0 Then
            cand = fso.BuildPath(Trim(dirs(i)), "pythonw.exe")
            If fso.FileExists(cand) Then
                FindPythonw = cand
                Exit Function
            End If
        End If
    Next

    base = shell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Programs\Python"
    If fso.FolderExists(base) Then
        For Each folder In fso.GetFolder(base).SubFolders
            cand = fso.BuildPath(folder.Path, "pythonw.exe")
            If fso.FileExists(cand) Then
                FindPythonw = cand
                Exit Function
            End If
        Next
    End If

    cand = shell.ExpandEnvironmentStrings("%WINDIR%") & "\pyw.exe"
    If fso.FileExists(cand) Then
        FindPythonw = cand
        Exit Function
    End If

    FindPythonw = ""
End Function
