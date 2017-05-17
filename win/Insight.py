#========================================================================================
#title           :Insigth.py
#description     :Connection with Emotiv Insigth and send the data through OSC protocol.
#date            :10/11/2016
#version         :0.1
#usage           :Run by the main
#python_version  :2.7
#========================================================================================


from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import pyqtSignal, pyqtSlot
import ctypes, time, OSC, sys, thread

class Insight(QtCore.QObject):

    # Signal of the GUI
    signalConnectStatus = pyqtSignal(bool)
    signalElectrodeStatus = pyqtSignal(int, int)
    signalSendText = pyqtSignal(str)

    def __init__(self):
        QtCore.QObject.__init__(self)
        self.setup()
        self.client = OSC.OSCClient()
        self.connect_client(host='127.0.0.1', port=9001)

    def connect_client(self, host='127.0.0.1', port=9001):
        self.client.connect((host, port))

    def setup(self):
        # ---------------------------------- Initial connection -----------------------------------------#
        self.libEDK = ctypes.cdll.LoadLibrary("edk64.dll")
        self.IEE_EmoEngineEventCreate = self.libEDK.IEE_EmoEngineEventCreate
        self.IEE_EmoEngineEventCreate.restype = ctypes.c_void_p
        self.eEvent = self.IEE_EmoEngineEventCreate()

        self.IS_GetTimeFromStart = self.libEDK.IS_GetTimeFromStart
        self.IS_GetTimeFromStart.argtypes = [ctypes.c_void_p]
        self.IS_GetTimeFromStart.restype = ctypes.c_float
        self.IS_GetWirelessSignalStatus = self.libEDK.IS_GetWirelessSignalStatus
        self.IS_GetWirelessSignalStatus.restype = ctypes.c_int
        self.IS_GetWirelessSignalStatus.argtypes = [ctypes.c_void_p]
        self.IS_GetContactQuality = self.libEDK.IS_GetContactQuality
        self.IS_GetContactQuality.restype = ctypes.c_int
        self.IS_GetContactQuality.argtypes = [ctypes.c_void_p, ctypes.c_int]

        self.IEE_EmoEngineEventGetEmoState = self.libEDK.IEE_EmoEngineEventGetEmoState
        self.IEE_EmoEngineEventGetEmoState.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        self.IEE_EmoEngineEventGetEmoState.restype = ctypes.c_int
        self.IEE_EmoStateCreate = self.libEDK.IEE_EmoStateCreate
        self.IEE_EmoStateCreate.restype = ctypes.c_void_p
        self.eState = self.IEE_EmoStateCreate()

        self.IEE_MotionDataCreate = self.libEDK.IEE_MotionDataCreate
        self.IEE_MotionDataCreate.restype = ctypes.c_void_p
        self.hMotionData = self.IEE_MotionDataCreate()

        # -------------------------------------- Initial values --------------------------------------------#
        self.userID = ctypes.c_uint(0)
        self.user = ctypes.pointer(self.userID)
        self.ready = 0
        self.state = ctypes.c_int(0)
        self.systemUpTime = ctypes.c_float(0.0)

        # Headset connection state
        self.batteryLevel = ctypes.c_long(0)
        self.batteryLevelP = ctypes.pointer(self.batteryLevel)
        self.maxBatteryLevel = ctypes.c_int(0)
        self.maxBatteryLevelP = ctypes.pointer(self.maxBatteryLevel)
        self.wirelessStrength = ctypes.c_int(0)

        # Electrodes: average bands power
        self.alphaValue = ctypes.c_double(0)
        self.low_betaValue = ctypes.c_double(0)
        self.high_betaValue = ctypes.c_double(0)
        self.gammaValue = ctypes.c_double(0)
        self.thetaValue = ctypes.c_double(0)
        self.alpha = ctypes.pointer(self.alphaValue)
        self.low_beta = ctypes.pointer(self.low_betaValue)
        self.high_beta = ctypes.pointer(self.high_betaValue)
        self.gamma = ctypes.pointer(self.gammaValue)
        self.theta = ctypes.pointer(self.thetaValue)
        self.channelList = [3, 7, 9, 12, 16]  # IED_AF3, IED_AF4, IED_T7, IED_T8, IED_Pz
        self.channelDict = {3: 'Af3', 7: 'Af4', 9: 'T7', 12: 'T8', 16: 'Pz'}
        self.channelDict2 = {3: 'FrontalLeft', 7: 'FrontalRight', 9: 'LateralLeft', 12: 'LateralRight', 16: 'Back'}
        self.channelStatus = {3: 0, 7: 0, 9: 0, 12:0, 16: 0}

        # Gyroscope, accelometer, magnetometer
        self.datarate = ctypes.c_uint(0)
        self.secs = ctypes.c_float(1)
        self.motionChannelList = [i for i in range(11)]
        self.motionNameList = ["COUNTER", "GYROX", "GYROY", "GYROZ", "ACCX", "ACCY", "ACCZ", "MAGX",
                           "MAGY", "MAGZ", "TIME"]

        # Performance metrics
        self.EyeX = ctypes.c_float(0)
        self.EyeY = ctypes.c_float(0)
        self.EyeLidLeft = ctypes.c_float(0)
        self.EyeLidRight = ctypes.c_float(0)

        self.X = ctypes.pointer(self.EyeX)
        self.Y = ctypes.pointer(self.EyeY)
        self.Left = ctypes.pointer(self.EyeLidLeft)
        self.Right = ctypes.pointer(self.EyeLidRight)

        self.RawScore = ctypes.c_double(0)
        self.MinScale = ctypes.c_double(0)
        self.MaxScale = ctypes.c_double(0)

        self.Raw = ctypes.pointer(self.RawScore)
        self.Min = ctypes.pointer(self.MinScale)
        self.Max = ctypes.pointer(self.MaxScale)
        self.performanceMetricsStates = {"Stress": [self.Raw, self.Min, self.Max], "Relaxation": [self.Raw, self.Min, self.Max],
                                         "Engagement": [self.Raw, self.Min, self.Max],
                                         "Interest": [self.Raw, self.Min, self.Max], "Focus": [self.Raw, self.Min, self.Max]}

        self.PM_EXCITEMENT = 0x0001,
        self.PM_RELAXATION = 0x0002,
        self.PM_STRESS = 0x0004,
        self.PM_ENGAGEMENT = 0x0008,
        self.PM_INTEREST = 0x0010,
        self.PM_FOCUS = 0x0020

        # Facial expressions
        self.FE_SURPRISE = 0x0020
        self.FE_FROWN = 0x0040
        self.FE_SMILE = 0x0080
        self.FE_CLENCH = 0x0100

        self.facialExpressionStates = {}
        self.facialExpressionStates[self.FE_FROWN] = 0
        self.facialExpressionStates[self.FE_SURPRISE] = 0
        self.facialExpressionStates[self.FE_SMILE] = 0
        self.facialExpressionStates[self.FE_CLENCH] = 0

    # -------------------------------------- Loading --------------------------------------------------#
        self.loadPerformanceMetrics()
        self.loadFacialExpressionFunctions()

    def start(self):
        while self.libEDK.IEE_EngineConnect("Emotiv Systems-5") != 0:
            self.signalSendText.emit("Searching an Emotiv Insight")
        self.signalSendText.emit("Connecting")
        while True:
            self.getEvent()
            time.sleep(0.01)

    def getEvent(self):
        try:
            self.state = self.libEDK.IEE_EngineGetNextEvent(self.eEvent)
            if self.state == 0:
                eventType = self.libEDK.IEE_EmoEngineEventGetType(self.eEvent)
                self.libEDK.IEE_EmoEngineEventGetUserId(self.eEvent, self.user)
                # Adding user
                if self.ready == 0 and eventType == 16:
                    self.ready = 1
                    self.signalSendText.emit("Ready")
                    #self.signalConnectStatus.emit(True)
                # Sending data
                if self.ready == 1:
                    # Headset status
                    if eventType == 64:
                        pass
                    thread.start_new_thread(self.getHeadsetStatus, (), {})
                    thread.start_new_thread(self.getPerformanceMetrics, (), {})
                    thread.start_new_thread(self.getFacialExpression, (), {})
                    thread.start_new_thread(self.getAverageBandPowers, (), {})
                    thread.start_new_thread(self.getMotionData, (), {})


        except Exception as e:
            print(e)

    def sendInsight2OSCmessage(self, text, value):
        message = OSC.OSCMessage()
        message.setAddress("/Insight/"+text)
        message.append(value)
        self.client.send(message)

    def getHeadsetStatus(self):
        self.libEDK.IEE_EmoEngineEventGetEmoState(self.eEvent, self.eState)
        self.systemUpTime = self.IS_GetTimeFromStart(self.eState)
        self.wirelessStrength = self.libEDK.IS_GetWirelessSignalStatus(self.eState)
        if self.wirelessStrength > 0:
            self.libEDK.IS_GetBatteryChargeLevel(self.eState, self.batteryLevelP, self.maxBatteryLevelP)
            for i in self.channelList:
                j = self.IS_GetContactQuality(self.eState, i)
                # i: the numer of the channel (3, 7, 9, 12, 16)
                # j: the quality of connection (0, 1, 2, 3, 4)
                self.signalElectrodeStatus.emit(i, j)
                self.channelStatus[i] = int(j > 2)
            thread.start_new_thread(self.sendInsight2OSCmessage, ("ChannelStatus", self.channelStatus.values()), {})
            thread.start_new_thread(self.sendInsight2OSCmessage, ("Battery", 100), {})
        thread.start_new_thread(self.sendInsight2OSCmessage, ("Wireless", self.wirelessStrength), {})

    def getAverageBandPowers(self):
        for i in self.channelList:
            thread.start_new_thread(self.getOneAverageBandPower, (i,), {})

    def getOneAverageBandPower(self, i):
        s = list()
        result = self.libEDK.IEE_GetAverageBandPowers(self.userID, i, self.theta, self.alpha, self.low_beta,
                                                      self.high_beta, self.gamma)
        if result == 0:  # EDK_OK
            if self.channelStatus[i] == 1:
                s = [round(self.alphaValue.value, 3),
                     round(self.low_betaValue.value, 3),
                     round(self.high_betaValue.value, 3),
                     round(self.gammaValue.value, 3),
                     round(self.thetaValue.value, 3)]
                self.sendInsight2OSCmessage(self.channelDict2[i], s)

    def getMotionData(self):
        self.libEDK.IEE_MotionDataUpdateHandle(self.userID, self.hMotionData)
        nSamplesTaken = ctypes.c_uint(0)
        nSamplesTakenP = ctypes.pointer(nSamplesTaken)
        self.libEDK.IEE_MotionDataGetNumberOfSample(self.hMotionData, nSamplesTakenP)
        if nSamplesTaken.value > 0:
            # sending
            dataType = ctypes.c_double * nSamplesTaken.value
            data = dataType()
            for sampleIdx in range(nSamplesTaken.value):

                gyroList = list()
                for i in [1, 2, 3]:
                    self.libEDK.IEE_MotionDataGet(self.hMotionData, i, data, nSamplesTaken.value)
                    gyroList.append(data[sampleIdx])
                self.sendInsight2OSCmessage("Gyro", gyroList)

                accelList = list()
                for i in [4, 5, 6]:
                    self.libEDK.IEE_MotionDataGet(self.hMotionData, i, data, nSamplesTaken.value)
                    accelList.append(data[sampleIdx])
                self.sendInsight2OSCmessage("Accel", accelList)

                magnList = list()
                for i in [7, 8, 9]:
                    self.libEDK.IEE_MotionDataGet(self.hMotionData, i, data, nSamplesTaken.value)
                    magnList.append(data[sampleIdx])
                self.sendInsight2OSCmessage("Magn", magnList)

    def loadFacialExpressionFunctions(self):
        self.IS_FacialExpressionIsBlink = self.libEDK.IS_FacialExpressionIsBlink
        self.IS_FacialExpressionIsBlink.restype = ctypes.c_int
        self.IS_FacialExpressionIsBlink.argtypes = [ctypes.c_void_p]

        self.IS_FacialExpressionIsLeftWink = self.libEDK.IS_FacialExpressionIsLeftWink
        self.IS_FacialExpressionIsLeftWink.restype = ctypes.c_int
        self.IS_FacialExpressionIsLeftWink.argtypes = [ctypes.c_void_p]

        self.IS_FacialExpressionIsRightWink = self.libEDK.IS_FacialExpressionIsRightWink
        self.IS_FacialExpressionIsRightWink.restype = ctypes.c_int
        self.IS_FacialExpressionIsRightWink.argtypes = [ctypes.c_void_p]

        self.IS_FacialExpressionGetUpperFaceAction = \
            self.libEDK.IS_FacialExpressionGetUpperFaceAction
        self.IS_FacialExpressionGetUpperFaceAction.restype = ctypes.c_int
        self.IS_FacialExpressionGetUpperFaceAction.argtypes = [ctypes.c_void_p]

        self.IS_FacialExpressionGetUpperFaceActionPower = \
            self.libEDK.IS_FacialExpressionGetUpperFaceActionPower
        self.IS_FacialExpressionGetUpperFaceActionPower.restype = ctypes.c_float
        self.IS_FacialExpressionGetUpperFaceActionPower.argtypes = [ctypes.c_void_p]

        self.IS_FacialExpressionGetLowerFaceAction = \
            self.libEDK.IS_FacialExpressionGetLowerFaceAction
        self.IS_FacialExpressionGetLowerFaceAction.restype = ctypes.c_int
        self.IS_FacialExpressionGetLowerFaceAction.argtypes = [ctypes.c_void_p]

        self.IS_FacialExpressionGetLowerFaceActionPower = \
            self.libEDK.IS_FacialExpressionGetLowerFaceActionPower
        self.IS_FacialExpressionGetLowerFaceActionPower.restype = ctypes.c_float
        self.IS_FacialExpressionGetLowerFaceActionPower.argtypes = [ctypes.c_void_p]

        self.IS_FacialExpressionGetEyeLocation = self.libEDK.IS_FacialExpressionGetEyeLocation
        self.IS_FacialExpressionGetEyeLocation.restype = ctypes.c_float
        self.IS_FacialExpressionGetEyeLocation.argtype = [ctypes.c_void_p]

        self.IS_FacialExpressionGetEyelidState = self.libEDK.IS_FacialExpressionGetEyelidState
        self.IS_FacialExpressionGetEyelidState.restype = ctypes.c_float
        self.IS_FacialExpressionGetEyelidState.argtype = [ctypes.c_void_p]


    def loadPerformanceMetrics(self):

        # short term excitement
        self.IS_PerformanceMetricGetInstantaneousExcitementModelParams = self.libEDK.IS_PerformanceMetricGetInstantaneousExcitementModelParams
        self.IS_PerformanceMetricGetInstantaneousExcitementModelParams.restype = ctypes.c_void_p
        self.IS_PerformanceMetricGetInstantaneousExcitementModelParams.argtypes = [ctypes.c_void_p]

        # relaxation
        self.IS_PerformanceMetricGetRelaxationModelParams = self.libEDK.IS_PerformanceMetricGetRelaxationModelParams
        self.IS_PerformanceMetricGetRelaxationModelParams.restype = ctypes.c_void_p
        self.IS_PerformanceMetricGetRelaxationModelParams.argtypes = [ctypes.c_void_p]

        # stress
        self.IS_PerformanceMetricGetStressModelParams = self.libEDK.IS_PerformanceMetricGetStressModelParams
        self.IS_PerformanceMetricGetStressModelParams.restype = ctypes.c_void_p
        self.IS_PerformanceMetricGetStressModelParams.argtypes = [ctypes.c_void_p]

        # boredom/engagement
        self.IS_PerformanceMetricGetEngagementBoredomModelParams = self.libEDK.IS_PerformanceMetricGetEngagementBoredomModelParams
        self.IS_PerformanceMetricGetEngagementBoredomModelParams.restype = ctypes.c_void_p
        self.IS_PerformanceMetricGetEngagementBoredomModelParams.argtypes = [ctypes.c_void_p]

        # interest
        self.IS_PerformanceMetricGetInterestModelParams = self.libEDK.IS_PerformanceMetricGetInterestModelParams
        self.IS_PerformanceMetricGetInterestModelParams.restype = ctypes.c_void_p
        self.IS_PerformanceMetricGetInterestModelParams.argtypes = [ctypes.c_void_p]

        # focus
        self.IS_PerformanceMetricGetFocusModelParams = self.libEDK.IS_PerformanceMetricGetFocusModelParams
        self.IS_PerformanceMetricGetFocusModelParams.restype = ctypes.c_void_p
        self.IS_PerformanceMetricGetFocusModelParams.argtypes = [ctypes.c_void_p]

        # Perfomance metrics Normalized Scores

        # long term excitement
        self.IS_PerformanceMetricGetExcitementLongTermScore = self.libEDK.IS_PerformanceMetricGetExcitementLongTermScore
        self.IS_PerformanceMetricGetExcitementLongTermScore.restype = ctypes.c_float
        self.IS_PerformanceMetricGetExcitementLongTermScore.argtypes = [ctypes.c_void_p]

        # short term excitement
        self.IS_PerformanceMetricGetInstantaneousExcitementScore = self.libEDK.IS_PerformanceMetricGetInstantaneousExcitementScore
        self.IS_PerformanceMetricGetInstantaneousExcitementScore.restype = ctypes.c_float
        self.IS_PerformanceMetricGetInstantaneousExcitementScore.argtypes = [ctypes.c_void_p]

        # relaxation
        self.IS_PerformanceMetricGetRelaxationScore = self.libEDK.IS_PerformanceMetricGetRelaxationScore
        self.IS_PerformanceMetricGetRelaxationScore.restype = ctypes.c_float
        self.IS_PerformanceMetricGetRelaxationScore.argtypes = [ctypes.c_void_p]

        # stress
        self.IS_PerformanceMetricGetStressScore = self.libEDK.IS_PerformanceMetricGetStressScore
        self.IS_PerformanceMetricGetStressScore.restype = ctypes.c_float
        self.IS_PerformanceMetricGetStressScore.argtypes = [ctypes.c_void_p]

        # boredom/engagement
        self.IS_PerformanceMetricGetEngagementBoredomScore = self.libEDK.IS_PerformanceMetricGetEngagementBoredomScore
        self.IS_PerformanceMetricGetEngagementBoredomScore.restype = ctypes.c_float
        self.IS_PerformanceMetricGetEngagementBoredomScore.argtypes = [ctypes.c_void_p]

        # interest
        self.IS_PerformanceMetricGetInterestScore = self.libEDK.IS_PerformanceMetricGetInterestScore
        self.IS_PerformanceMetricGetInterestScore.restype = ctypes.c_float
        self.IS_PerformanceMetricGetInterestScore.argtypes = [ctypes.c_void_p]

        # focus
        self.IS_PerformanceMetricGetFocusScore = self.libEDK.IS_PerformanceMetricGetFocusScore
        self.IS_PerformanceMetricGetFocusScore.restype = ctypes.c_float
        self.IS_PerformanceMetricGetFocusScore.argtypes = [ctypes.c_void_p]

    def getFacialExpression(self):
        # binary response: return 0 or 1.
        blink = self.IS_FacialExpressionIsBlink(self.eState)
        left_wink = self.IS_FacialExpressionIsLeftWink(self.eState)
        right_wink = self.IS_FacialExpressionIsRightWink(self.eState)

        thread.start_new_thread(self.sendInsight2OSCmessage, ("Blink", blink), {})
        thread.start_new_thread(self.sendInsight2OSCmessage, ("LeftWink", left_wink), {})
        thread.start_new_thread(self.sendInsight2OSCmessage, ("RightWink", right_wink), {})

        # response between 0 and 1. Search the upper and lower facial expression.
        upperFaceAction = self.IS_FacialExpressionGetUpperFaceAction(self.eState)
        upperFacePower = self.IS_FacialExpressionGetUpperFaceActionPower(self.eState)
        lowerFaceAction = self.IS_FacialExpressionGetLowerFaceAction(self.eState)
        lowerFacePower = self.IS_FacialExpressionGetLowerFaceActionPower(self.eState)

        # TODO: ask about this in the next meeting (adapar)
        self.facialExpressionStates[upperFaceAction] = upperFacePower
        self.facialExpressionStates[lowerFaceAction] = lowerFacePower

        thread.start_new_thread(self.sendInsight2OSCmessage,
                                ("Surprise", self.facialExpressionStates[self.FE_SURPRISE]), {})
        thread.start_new_thread(self.sendInsight2OSCmessage,
                                ("Furrow", self.facialExpressionStates[self.FE_FROWN]), {})
        thread.start_new_thread(self.sendInsight2OSCmessage,
                                ("Smile", self.facialExpressionStates[self.FE_SMILE]), {})
        thread.start_new_thread(self.sendInsight2OSCmessage,
                                ("Clench", self.facialExpressionStates[self.FE_CLENCH]), {})

        self.IS_FacialExpressionGetEyeLocation(self.eState, self.X, self.Y)
        thread.start_new_thread(self.sendInsight2OSCmessage, ("Eye", [self.EyeX.value, self.EyeY.value]), {})

        self.IS_FacialExpressionGetEyelidState(self.eState, self.Left, self.Right)
        thread.start_new_thread(self.sendInsight2OSCmessage, ("EyeLid", [self.EyeLidLeft.value, self.EyeLidRight.value]), {})

    def getPerformanceMetrics(self):
        # Perfomance metrics Model Parameters /long term excitement not present

        # excitement
        #self.IS_PerformanceMetricGetExcitementLongTermScore(self.eState)
        #self.IS_PerformanceMetricGetInstantaneousExcitementScore(self.eState)
        #self.IS_PerformanceMetricGetInstantaneousExcitementModelParams(self.eState, self.Raw, self.Min, self.Max)
        #self.performanceMetricsStates["Excitement"] = [self.RawScore.value, self.MinScale.value, self.MaxScale.value]
        #self.sendInsight2OSCmessage("Excitement", [self.RawScore.value, self.MinScale.value, self.MaxScale.value])

        # stress
        self.IS_PerformanceMetricGetStressModelParams(self.eState, self.Raw, self.Min, self.Max)
        self.performanceMetricsStates["Stress"] = [self.RawScore.value, self.MinScale.value, self.MaxScale.value]
        self.sendInsight2OSCmessage("Stress", [self.RawScore.value, self.MinScale.value, self.MaxScale.value])


        # relaxation
        self.IS_PerformanceMetricGetRelaxationScore(self.eState)
        self.IS_PerformanceMetricGetRelaxationModelParams(self.eState, self.Raw, self.Min, self.Max)
        self.performanceMetricsStates["Relaxation"] = [self.RawScore.value, self.MinScale.value, self.MaxScale.value]
        self.sendInsight2OSCmessage("Relaxation", [self.RawScore.value, self.MinScale.value, self.MaxScale.value])

        # engagement
        self.IS_PerformanceMetricGetEngagementBoredomScore(self.eState)
        self.IS_PerformanceMetricGetEngagementBoredomModelParams(self.eState, self.Raw, self.Min, self.Max)
        self.performanceMetricsStates["Engagement"] = [self.RawScore.value, self.MinScale.value, self.MaxScale.value]
        self.sendInsight2OSCmessage("Engagement", [self.RawScore.value, self.MinScale.value, self.MaxScale.value])

        # interest
        self.IS_PerformanceMetricGetInterestScore(self.eState)
        self.IS_PerformanceMetricGetInterestModelParams(self.eState, self.Raw, self.Min, self.Max)
        self.performanceMetricsStates["Interest"] = [self.RawScore.value, self.MinScale.value, self.MaxScale.value]
        self.sendInsight2OSCmessage("Interest", [self.RawScore.value, self.MinScale.value, self.MaxScale.value])

        # focus
        self.IS_PerformanceMetricGetFocusScore(self.eState)
        self.IS_PerformanceMetricGetFocusModelParams(self.eState, self.Raw, self.Min, self.Max)
        self.performanceMetricsStates["Focus"] = [self.RawScore.value, self.MinScale.value, self.MaxScale.value]
        self.sendInsight2OSCmessage("Focus", [self.RawScore.value, self.MinScale.value, self.MaxScale.value])

        print(self.performanceMetricsStates)
        #print(self.eState)

    def disconnect(self):
        self.libEDK.IEE_EngineDisconnect()
        self.libEDK.IEE_EmoStateFree(self.eState)
        self.libEDK.IEE_EmoEngineEventFree(self.eEvent)

