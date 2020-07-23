#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <msi.h>
#include <shlobj.h>

UINT WINAPI
CallSHChangeNotifyAssocChanged(MSIHANDLE hInstall)
{
    (void)hInstall;

    SHChangeNotify(SHCNE_ASSOCCHANGED, SHCNF_IDLIST, 0, 0);
    return ERROR_SUCCESS;
}

BOOL WINAPI
DllMainCRTStartup(HINSTANCE hinstDLL,
                  DWORD     fdwReason,
                  LPVOID    lpvReserved)
{
    (void)hinstDLL; (void)fdwReason; (void)lpvReserved;

    return TRUE;
}
