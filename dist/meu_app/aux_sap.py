import time
import subprocess
import win32com.client as win32
import os


def login_sap():
    try:
        os.system('taskkill /f /im  saplogon.exe')
    except:
        pass
    path = r"C:\Program Files (x86)\SAP\FrontEnd\SAPgui\saplogon.exe"
    subprocess.Popen(path)
    time.sleep(5)
    SapGuiAuto = win32.GetObject("SAPGUI")
    application = SapGuiAuto.GetScriptingEngine
    connection = application.OpenConnection('SBP - ERP ECC - Produção', True)  # 'ECT - ERP ECC - Qualidade'
    time.sleep(3)
    session_0 = connection.Children(0)
    return session_0


def close_sap():
    os.system('taskkill /f /im  saplogon.exe')


def permite_e_liberar(dataframe):
    session = login_sap()
    """PERMITE"""
    dataframe['Nº Ordem'].to_clipboard(index=False, header=False)
    session.findById("wnd[0]/tbar[0]/okcd").text = "/NZIPM2"
    session.findById("wnd[0]").sendVKey(0)
    session.findById("wnd[0]/tbar[1]/btn[17]").press()
    session.findById("wnd[1]/usr/txtV-LOW").text = "lim_permit"
    session.findById("wnd[1]/usr/txtENAME-LOW").text = ""
    session.findById("wnd[1]/tbar[0]/btn[8]").press()
    session.findById("wnd[0]/usr/btn%_S_AUFNR_%_APP_%-VALU_PUSH").press()
    session.findById("wnd[1]/tbar[0]/btn[24]").press()
    session.findById("wnd[1]/tbar[0]/btn[8]").press()
    session.findById("wnd[0]/tbar[1]/btn[8]").press()
    try:
        session.findById("wnd[0]/usr/cntlGRID1/shellcont/shell").setCurrentCell(-1, "")
        session.findById("wnd[0]/usr/cntlGRID1/shellcont/shell").selectColumn("LIGHTS")
        session.findById("wnd[0]/usr/cntlGRID1/shellcont/shell").selectAll()
        session.findById("wnd[0]/tbar[1]/btn[42]").press()
        session.findById("wnd[1]/tbar[0]/btn[0]").press()
    except:
        session.findById("wnd[1]/tbar[0]/btn[0]").press()  # Se não tiver nenhuma que precisa de permite
    """LIBERAR"""
    df_aber = dataframe[dataframe['Stat. Sist.'].str.contains('ABER')]
    if not df_aber.empty:
        df_aber['Nº Ordem'].to_clipboard(index=False, header=False)
        session.findById("wnd[0]/tbar[0]/okcd").text = "/nziw38"
        session.findById("wnd[0]").sendVKey(0)
        session.findById("wnd[0]/tbar[1]/btn[17]").press()
        session.findById("wnd[1]/usr/txtV-LOW").text = "OS_PERMITE"
        session.findById("wnd[1]/usr/txtENAME-LOW").text = ""
        session.findById("wnd[1]/tbar[0]/btn[8]").press()
        session.findById("wnd[0]/usr/btn%_AUFNR_%_APP_%-VALU_PUSH").press()
        session.findById("wnd[1]/tbar[0]/btn[24]").press()
        session.findById("wnd[1]/tbar[0]/btn[8]").press()
        try:
            session.findById("wnd[0]/tbar[1]/btn[8]").press()
            session.findById("wnd[0]/usr/cntlGRID1/shellcont/shell").setCurrentCell(-1, "")
            session.findById("wnd[0]/usr/cntlGRID1/shellcont/shell").selectAll()
            session.findById("wnd[0]/tbar[1]/btn[17]").press()
            session.findById("wnd[0]/tbar[1]/btn[44]").press()

            for ordem in df_aber['Nº Ordem']:
                try:
                    session.findById("wnd[1]/usr/btnSPOP-OPTION2").press()  # Não aceitar ERRD
                    session.findById("wnd[0]/tbar[0]/btn[11]").press()      # Salvar
                except:
                    try:
                        session.findById("wnd[1]/usr/btnOPTION2").press()  # Erro caso esteja bloq ou já Lib
                        session.findById("wnd[0]/tbar[0]/btn[3]").press()  # Volta para tela de Ordens
                    except:
                        try:
                            session.findById("wnd[1]/tbar[0]/btn[0]").press()  # Fechar Pop Up
                            session.findById("wnd[0]/tbar[0]/btn[3]").press()  # Voltar
                        except:
                            try:
                                session.findById("wnd[0]/tbar[0]/btn[3]").press()  # Voltar
                            except:
                                pass
        except:
            session.findById("wnd[1]/tbar[0]/btn[0]").press()  # Se não encontrar nenhuma das ordens

    close_sap()
