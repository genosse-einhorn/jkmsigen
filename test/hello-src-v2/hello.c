#include <windows.h>

EXTERN_C void WINAPI
msvcWinMainCRTStartup()
{
    MessageBoxA(NULL, "Hello, World! (v2)", "Hello", MB_OK|MB_ICONASTERISK);

    ExitProcess(0);
}

