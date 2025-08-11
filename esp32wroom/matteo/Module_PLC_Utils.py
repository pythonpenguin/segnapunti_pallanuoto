import time

class PLC_CntDw(object):
    def __init__(self):
        self.StartTime = time.ticks_ms()
        self.ActTime = time.ticks_ms()
        self.execCnt = False
        self.doneCnt = False
        self.remMs = 0
        self.selMs = 0

    def TON_rsx(self,selMs):
        self.StartTime = time.ticks_ms()
        self.ActTime = time.ticks_ms()
        self.execCnt = True
        self.doneCnt = False
        self.remMs = selMs
        self.selMs = selMs

    def TON_exec(self,selRun):
        self.ActTime = time.ticks_ms()
        if (self.execCnt):
            DiffTime = int(round((self.ActTime - self.StartTime)))
            if (DiffTime<0):
                self.StartTime = time.ticks_ms()
                self.ActTime = time.ticks_ms()
                self.selMs = self.remMs
                DiffTime = 0
            if (selRun):
                if(DiffTime>self.selMs):
                    self.doneCnt = True
                    self.execCnt = False
                    self.remMs = 0
                else:
                    self.remMs = self.selMs-DiffTime
            else:
                self.StartTime = time.ticks_ms()
                self.ActTime = time.ticks_ms()
                self.selMs = self.remMs
        else:
            self.StartTime = time.ticks_ms()
            self.ActTime = time.ticks_ms()
            self.remMs = 0
            self.selMs = 0

class PLC_Ton(object):
    def __init__(self):
        self.StartTime = time.ticks_ms()
        self.ActTime = time.ticks_ms()
        self.Q = False
        self.ET = 0

    def TON_ex(self,INval,PT):
        self.ActTime = time.ticks_ms()
        DiffTime = int(round((self.ActTime - self.StartTime)))
        if (DiffTime<0):
            DiffTime = 0
            self.StartTime = self.ActTime
        if (INval):
            if(DiffTime>PT):
                self.Q = True
                self.ET = PT
            else:
                self.ET = DiffTime
        else:
            self.StartTime = self.ActTime
            self.Q = False
            self.ET = 0

    def TON_rsx(self):
        self.StartTime = time.ticks_ms()
        self.Q = False
        self.ET = 0

class PLC_Toff(object):
    def __init__(self):
        self.StartTime = time.ticks_ms()
        self.ActTime = time.ticks_ms()
        self.Q = False
        self.ET = 0

    def TOFF_ex(self,INval,PT):
        self.ActTime = time.ticks_ms()
        DiffTime = int(round((self.ActTime - self.StartTime)))
        if (DiffTime<0):
            DiffTime = 0
            self.StartTime = self.ActTime
        if (INval):
            self.StartTime = self.ActTime
            self.Q = True
            self.ET = 0
        else:
            if(DiffTime>PT):
                self.Q = False
                self.ET = PT
            else:
                self.ET = DiffTime


    def TOFF_rsx(self):
        self.StartTime = time.ticks_ms()
        self.Q = False
        self.ET = 0

class PLC_RTrig(object):
    def __init__(self):
        self.CLKsvd = False
        self.Q = False

    def R_TRIG_ex(self,CLK):
        if (CLK and (not self.CLKsvd)):
            self.Q = True
        else:
            self.Q = False

        self.CLKsvd = CLK

class PLC_FTrig(object):
    def __init__(self):
        self.CLKsvd = False
        self.Q = False

    def F_TRIG_ex(self,CLK):
        if ((not CLK) and self.CLKsvd):
            self.Q = True
        else:
            self.Q = False

        self.CLKsvd = CLK

def GetBit(bytevalue, bitpos):
    maskval = bytevalue
    filteredval = 0
    if (bitpos>0):
        for GBi in range (0,bitpos):
            maskval=(maskval-(maskval%2))/2
    filteredval = maskval % 2
    if (filteredval>0):
        return True
    else:
        return False

def GetBitOld(bytevalue, bitpos):
    maskval = 1
    for GBi in range (0,bitpos):
        maskval=maskval*2
    filteredval=bytevalue & maskval
    if (filteredval>0):
        return True
    else:
        return False

def SetBit(oldbytevalue, bitpos, newvalue):
    maskval = bytevalue
    remval = 1
    filteredval = 0
    if (bitpos>0):
        for GBi in range (0,bitpos):
            maskval=(maskval-(maskval%2))/2
            remval=remval*2
    filteredval = maskval % 2
    maskval = bytevalue
    if (filteredval>0):
        maskval=maskval-remval
    if (newvalue):
        maskval=maskval+remval
    return maskval

def SetBitOld(oldbytevalue, bitpos, newvalue):
    maskval = 1
    filteredval = 0
    for GBi in range (0,bitpos):
        maskval=maskval*2
    if (newvalue):
        filteredval=oldbytevalue | maskval
    else:
        filteredval=oldbytevalue & (255-maskval)
    return filteredval

def BitMerge(B7,B6,B5,B4,B3,B2,B1,B0):
    maskval = 0
    if (B7): maskval = maskval + 1
    maskval = maskval * 2
    if (B6): maskval = maskval + 1
    maskval = maskval * 2
    if (B5): maskval = maskval + 1
    maskval = maskval * 2
    if (B4): maskval = maskval + 1
    maskval = maskval * 2
    if (B3): maskval = maskval + 1
    maskval = maskval * 2
    if (B2): maskval = maskval + 1
    maskval = maskval * 2
    if (B1): maskval = maskval + 1
    maskval = maskval * 2
    if (B0): maskval = maskval + 1

    return maskval

def IntToBool(bytevalue):
    if (bytevalue>0):
        return True
    else:
        return False
