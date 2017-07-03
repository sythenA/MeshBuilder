
import _winreg
import subprocess
from commonDialog import onCritical
import os.path


def loadParaView():
    try:
        reg = _winreg.ConnectRegistry(None, _winreg.HKEY_LOCAL_MACHINE)
        k = _winreg.OpenKey(reg, r'SOFTWARE\WOW6432Node\Kitware, Inc.')
        pathKey = _winreg.EnumKey(k, 0)
        pathName = _winreg.QueryValue(k, pathKey)

        subprocess.call([os.path.join(pathName, 'bin\\paraview.exe')])
    except:
        onCritical(123)
