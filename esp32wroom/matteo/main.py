import asyncio
import gc
import machine
import time

import config
from microdot import Microdot, send_file

import Module_PLC_Utils as Utils


#*************************************************************************************************************************************
#INIT APPLICATION ********************************************************************************************************************
#*************************************************************************************************************************************
app = Microdot()

testBoard = True
tableCounterDuration = 30000
tableCounterReset = 1
tableCounterRun = 0
tableCounterXX = 0
tableSirenDuration = 2000
tableSirenX = 0

#*************************************************************************************************************************************
#WIFI MANAGEMENT *********************************************************************************************************************
#*************************************************************************************************************************************
def wifi_connect():
    """Connect to the configured Wi-Fi network.
    Returns the IP address of the connected interface.
    """
    import network

    ap_if = network.WLAN(network.AP_IF)
    ap_if.active(False)

    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect(config.WIFI_ESSID, config.WIFI_PASSWORD)
        for i in range(20):
            if sta_if.isconnected():
                break
            time.sleep(1)
        if not sta_if.isconnected():
            raise RuntimeError('Could not connect to network')
    return sta_if.ifconfig()[0]


#*************************************************************************************************************************************
#WEB SOCKETS MANAGEMENT **************************************************************************************************************
#*************************************************************************************************************************************
@app.route('/')
async def index(request):
    return send_file('index.html')


@app.route('/api')
async def api(request):
    global testBoard
    global tableCounterDuration
    global tableCounterReset
    global tableCounterRun
    global tableCounterXX
    global tableSirenDuration
    global tableSirenX

    if 'newTime' in request.args:
        tableCounterDuration = int(request.args['newTime'])
        tableCounterReset = 1
    if 'exeTime' in request.args:
        tableCounterRun = int(request.args['exeTime'])
    if 'exeSiren' in request.args:
        tableSirenDuration = int(request.args['exeSiren'])
        tableSirenX = 1
    return {
        'tableCounterXX': tableCounterXX,
        'tableSirenX': tableSirenX,
    }


#*************************************************************************************************************************************
#APP MANAGEMENT **********************************************************************************************************************
#*************************************************************************************************************************************
async def app_start_operations():
    global testBoard
    global tableCounterDuration
    global tableCounterReset
    global tableCounterRun
    global tableCounterXX
    global tableSirenDuration
    global tableSirenX

    # Led manager
    #input data
    LedMan_xPrintData = False
    LedMan_byValueXU = 0
    LedMan_byValueDX = 0
    LedMan_xBuzz = False
    #local data
    LedMan_xUpdateData = False
    LedMan_iDrawPos = 0
    LedMan_pin_Buzz = machine.Pin(16, machine.Pin.OUT)#, drive=machine.Pin.DRIVE_3)
    #LedMan_pin_BuzzLed = machine.Pin(23, machine.Pin.OUT, drive=machine.Pin.DRIVE_3)
    LedMan_pin_DX = machine.Pin(25, machine.Pin.OUT)#, drive=machine.Pin.DRIVE_3)
    LedMan_pin_XU = machine.Pin(33, machine.Pin.OUT)#, drive=machine.Pin.DRIVE_3)
    LedMan_pin_A = machine.Pin(26, machine.Pin.OUT)#, drive=machine.Pin.DRIVE_3)
    LedMan_pin_B = machine.Pin(14, machine.Pin.OUT)#, drive=machine.Pin.DRIVE_3)
    LedMan_pin_C = machine.Pin(27, machine.Pin.OUT)#, drive=machine.Pin.DRIVE_3)
    LedMan_pin_D = machine.Pin(12, machine.Pin.OUT)#, drive=machine.Pin.DRIVE_3)
    LedMan_fbUpdateStep_TON = Utils.PLC_Ton()

    # App manager
    fbtableCounterUpdate_TON = Utils.PLC_Ton()
    fbTableSirenUpdate_TON = Utils.PLC_Ton()
    fbTableCountDown = Utils.PLC_CntDw()
    fbTableCountDown_Done_RE = Utils.PLC_RTrig()

    while True:
        """
            LED MANAGER ***********************************************************************************
        """
        try:
            if (not(testBoard)):
                """
                    buzzer update
                """
                #print("status xBuzz: ", LedMan_xBuzz)  # Print the received data
                #print("status byValueXU: ", LedMan_byValueXU)  # Print the received data
                #print("status byValueDX: ", LedMan_byValueDX)  # Print the received data
                #print("status A: ", LedMan_pin_A.value())  # Print the received data
                #print("status B: ", LedMan_pin_B.value())  # Print the received data
                #print("status C: ", LedMan_pin_C.value())  # Print the received data
                #print("status D: ", LedMan_pin_D.value())  # Print the received data
                #if (LedMan_xBuzz):                          LedMan_pin_BuzzLed.value(1)
                #else:                                       LedMan_pin_BuzzLed.value(0)
                if (LedMan_xBuzz):                          LedMan_pin_Buzz.value(1)
                else:                                       LedMan_pin_Buzz.value(0)

                """
                    draw update
                """
                LedMan_iDrawPos = LedMan_iDrawPos
                if (LedMan_xPrintData and (LedMan_iDrawPos==0)):
                    LedMan_xPrintData = False
                    LedMan_xUpdateData = True

                """
                    step beat
                """
                LedMan_fbUpdateStep_TON.TON_ex((not(LedMan_fbUpdateStep_TON.Q)),5)
                if (LedMan_fbUpdateStep_TON.Q and (LedMan_xUpdateData or (LedMan_iDrawPos>0))):
                    LedMan_xUpdateData = False
                    LedMan_iDrawPos = (LedMan_iDrawPos+1) % 7
                if (LedMan_fbUpdateStep_TON.Q == True):
                    LedMan_fbUpdateStep_TON.TON_rsx()

                """
                    step update
                """
                if (LedMan_iDrawPos==1):
                    if (LedMan_byValueXU & 1):   LedMan_pin_A.value(1)
                    else:                        LedMan_pin_A.value(0)
                    if (LedMan_byValueXU & 2):   LedMan_pin_B.value(1)
                    else:                        LedMan_pin_B.value(0)
                    if (LedMan_byValueXU & 4):   LedMan_pin_C.value(1)
                    else:                        LedMan_pin_C.value(0)
                    if (LedMan_byValueXU & 8):   LedMan_pin_D.value(1)
                    else:                        LedMan_pin_D.value(0)
                elif (LedMan_iDrawPos==2):
                    LedMan_pin_XU.value(0)
                elif (LedMan_iDrawPos==3):
                    LedMan_pin_XU.value(1)
                elif (LedMan_iDrawPos==4):
                    if (LedMan_byValueDX & 1):   LedMan_pin_A.value(1)
                    else:                        LedMan_pin_A.value(0)
                    if (LedMan_byValueDX & 2):   LedMan_pin_B.value(1)
                    else:                        LedMan_pin_B.value(0)
                    if (LedMan_byValueDX & 4):   LedMan_pin_C.value(1)
                    else:                        LedMan_pin_C.value(0)
                    if (LedMan_byValueDX & 8):   LedMan_pin_D.value(1)
                    else:                        LedMan_pin_D.value(0)
                elif (LedMan_iDrawPos==5):
                    LedMan_pin_DX.value(0)
                elif (LedMan_iDrawPos==6):
                    LedMan_pin_DX.value(1)

                """
                    led manager end
                """

            else:
                """
                    test manager
                """

                if (LedMan_xBuzz):               LedMan_pin_Buzz.value(1)
                else:                            LedMan_pin_Buzz.value(0)
                if (LedMan_byValueXU & 1):       LedMan_pin_D.value(1)
                else:                            LedMan_pin_D.value(0)
                if (LedMan_byValueXU & 2):       LedMan_pin_B.value(1)
                else:                            LedMan_pin_B.value(0)
                if (LedMan_byValueXU & 4):       LedMan_pin_C.value(1)
                else:                            LedMan_pin_C.value(0)
                if (LedMan_byValueXU & 8):       LedMan_pin_A.value(1)
                else:                            LedMan_pin_A.value(0)

                """
                    test manager end
                """

        #except asyncio.CancelledError:
        #    pass
        except Exception as error:
            print(f'Could not execute software, error: {error}')
        else:
            pass


        """
            APP MANAGER ***********************************************************************************
        """
        try:
            """
                counter manager
            """
            if (tableCounterReset>0):
                tableCounterReset = 0
                fbTableCountDown.TON_rsx(tableCounterDuration)
            fbTableCountDown.TON_exec(tableCounterRun>0)
            actTimeCtdw = fbTableCountDown.remMs
            calcTimeCtdw = (actTimeCtdw-(actTimeCtdw%1000))/1000
            tableCounterXX = int(calcTimeCtdw)
            fbTableCountDown_Done_RE.R_TRIG_ex(fbTableCountDown.doneCnt)
            if (fbTableCountDown_Done_RE.Q):
                tableSirenDuration = 2000
                tableSirenX = 1

            """
                update manager
            """
            #print("tableCounterXX: ", fbTableCountDown.remMs/1000)  # Print the received data
            #print("tableCounterXX: ", tableCounterXX)  # Print the received data
            #print("LedMan_xBuzz: ", LedMan_xBuzz)  # Print the received data
            fbtableCounterUpdate_TON.TON_ex((not(fbtableCounterUpdate_TON.Q)),100)
            if (fbtableCounterUpdate_TON.Q == True):
                fbtableCounterUpdate_TON.TON_ex(False,1000)
                fbtableCounterUpdate_TON.TON_ex(True,1000)

                LedMan_byValueXU=int(tableCounterXX % 10)
                LedMan_byValueDX=int(((tableCounterXX-(tableCounterXX % 10))/10) % 10)
                LedMan_xPrintData = True
                #print("tableCounterXX: ", tableCounterXX)  # Print the received data
                #print("tableSirenX: ", tableSirenX)  # Print the received data

            """
                buzzer manager
            """
            LedMan_xBuzz = (tableSirenX>0)
            fbTableSirenUpdate_TON.TON_ex(LedMan_xBuzz,tableSirenDuration)
            if (fbTableSirenUpdate_TON.Q == True):
                tableSirenX = 0
                LedMan_xBuzz = (tableSirenX>0)

            """
                app manager end
            """

        #except asyncio.CancelledError:
        #    pass
        except Exception as error:
            print(f'Could not execute software, error: {error}')
        else:
            pass

        gc.collect()
        await asyncio.sleep(0.005)

#*************************************************************************************************************************************
#GLOBAL MANAGEMENT *******************************************************************************************************************
#*************************************************************************************************************************************
async def start():
    ip = wifi_connect()
    print(f'Starting server at http://{ip}:8000...')
    bgtask = asyncio.create_task(app_start_operations())
    server = asyncio.create_task(app.start_server(port=8000))
    await asyncio.gather(server, bgtask)

asyncio.run(start())
