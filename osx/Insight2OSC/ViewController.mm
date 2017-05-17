//
//  ViewController.m
//  Insight2OSC
//
//  Created by Cuong Trinh on 11/19/15.
//  Copyright © 2015 Emotiv. All rights reserved.
//

#import "ViewController.h"
#import <edk/Iedk.h>
#import <edk/IEmoStateDLL.h>
#import <OSCKit/OSCKit.h>

#include <iostream>

#define IS_THREADED

BOOL isConnected = NO;
BOOL sendBandPowerData = YES;
BOOL sendMotionData = YES;
BOOL sendFacialData = YES;

IEE_DataChannel_t ChannelList[] = {
    IED_AF3, IED_AF4, IED_T7, IED_T8, IED_Pz
};

IEE_InputChannels_t InputChannelList[] = {
    IEE_CHAN_AF3, IEE_CHAN_AF4, IEE_CHAN_T7, IEE_CHAN_T8, IEE_CHAN_Pz
};

typedef enum {
    BAND_THETA,
    BAND_ALPHA,
    BAND_BETA_LOW,
    BAND_BETA_HIGH,
    BAND_GAMMA,
    BAND_NONE
} FrequencyBands;

IEE_MotionDataChannel_t gyroChannelList[]   = { IMD_GYROX, IMD_GYROY, IMD_GYROZ };
IEE_MotionDataChannel_t accChannelList[]    = { IMD_ACCX, IMD_ACCY, IMD_ACCZ };
IEE_MotionDataChannel_t magChannelList[]    = { IMD_MAGX,IMD_MAGY,IMD_MAGZ };

@implementation ViewController

EmoEngineEventHandle eEvent;
EmoStateHandle eState;
DataHandle hData;

unsigned int userID					= 0;
float motionDataBufferSizeInSecs	= 1;
bool readyToCollect					= YES;

NSFileHandle *file;
NSMutableData *data;

- (void)viewDidLoad {
    [super viewDidLoad];
    
    self.clientIP.stringValue = @"127.0.0.1";
    self.clientPort.stringValue = @"7000";
    
    NSArray *paths = NSSearchPathForDirectoriesInDomains(NSDocumentDirectory,
                                                         NSUserDomainMask,
                                                         YES);
    documentDirectory = [paths lastObject];
    
    name_channel = [[NSArray alloc]initWithObjects:@"AF3",@"AF4",@"T7",@"T8",@"Pz", nil];
    non_standard_name_channel = [[NSArray alloc]initWithObjects:@"FrontalLeft",@"FrontalRight",@"LateralLeft",@"LateralRight",@"Back", nil];
    
    [self setupInsight];

    [NSTimer scheduledTimerWithTimeInterval:1.0 target:self selector:@selector(connectDevice) userInfo:nil repeats:YES];
#ifdef IS_THREADED
    [NSThread detachNewThreadSelector:@selector(getNextEvent) toTarget:self withObject:nil];
    [NSThread detachNewThreadSelector:@selector(updateChannelSignalQuality) toTarget:self withObject:nil];
#else
    [NSTimer scheduledTimerWithTimeInterval:0.01 target:self selector:@selector(getNextEvent) userInfo:nil repeats:YES];
    [NSTimer scheduledTimerWithTimeInterval:0.50 target:self selector:@selector(updateChannelSignalQuality) userInfo:nil repeats:YES];
#endif
}

- (void)setRepresentedObject:(id)representedObject {
    [super setRepresentedObject:representedObject];

    // Update the view, if already loaded.
}

-(void) setupInsight {
    eEvent	= IEE_EmoEngineEventCreate();
    eState	= IEE_EmoStateCreate();
    hData   = IEE_MotionDataCreate();

    IEE_EmoInitDevice();
    IEE_EmoInitDevice();
    
    if( IEE_EngineConnect() != EDK_OK ) {
        //TODO: Put some status here
    }
    
    IEE_MotionDataSetBufferSizeInSec(motionDataBufferSizeInSecs);
}

-(void) updateChannelSignalQuality {
#ifdef IS_THREADED
    while (true) {
#endif
        if (readyToCollect) {
            IEE_EEG_ContactQuality_t contactQuality;
            
            for(int i=0 ; i < sizeof(InputChannelList)/sizeof(IEE_InputChannels_t) ; ++i) {
                contactQuality = IS_GetContactQuality(eState, InputChannelList[i]);
                switch (contactQuality) {
                    case IEEG_CQ_NO_SIGNAL:
                        [self setChannelSignalQualityImage:@"StatusLightGray" for:InputChannelList[i]];
                        break;
                    case IEEG_CQ_VERY_BAD:
                    case IEEG_CQ_POOR:
                        [self setChannelSignalQualityImage:@"StatusLightRed" for:InputChannelList[i]];
                        break;
                    case IEEG_CQ_FAIR:
                        [self setChannelSignalQualityImage:@"StatusLightYellow" for:InputChannelList[i]];
                        break;
                    case IEEG_CQ_GOOD:
                        [self setChannelSignalQualityImage:@"StatusLightGreen" for:InputChannelList[i]];
                        break;
                }
            }
        } else {
            self.electrodeStatusImageAF3.image = [NSImage imageNamed:@"StatusLightGray"];
            self.electrodeStatusImageAF4.image = [NSImage imageNamed:@"StatusLightGray"];
            self.electrodeStatusImageT7.image = [NSImage imageNamed:@"StatusLightGray"];
            self.electrodeStatusImageT8.image = [NSImage imageNamed:@"StatusLightGray"];
            self.electrodeStatusImagePz.image = [NSImage imageNamed:@"StatusLightGray"];
        }
#ifdef IS_THREADED
    }
#endif
}

-(void) setChannelSignalQualityImage:(nonnull NSString *)image for:(IEE_InputChannels_t)channel {
    switch (channel) {
        case IED_AF3:
            self.electrodeStatusImageAF3.image = [NSImage imageNamed:image];
            break;
        case IED_AF4:
            self.electrodeStatusImageAF4.image = [NSImage imageNamed:image];
            break;
        case IED_T7:
            self.electrodeStatusImageT7.image = [NSImage imageNamed:image];
            break;
        case IED_T8:
            self.electrodeStatusImageT8.image = [NSImage imageNamed:image];
            break;
        case IED_Pz:
            self.electrodeStatusImagePz.image = [NSImage imageNamed:image];
            break;
        default:
            break;
    }
}

-(void) connectDevice {
    /*Connect with Insight headset in mode Bluetooth*/

    int numberDevice = IEE_GetInsightDeviceCount();
    if(numberDevice > 0 && !isConnected) {
        IEE_ConnectInsightDevice(0);
        isConnected = YES;
    }
    else isConnected = NO;
}

-(void) getNextEvent {
#ifdef IS_THREADED
    while (true) {
#endif
        int state = IEE_EngineGetNextEvent(eEvent);
        unsigned int userID = 0;
        
        IEE_EmoEngineEventGetEmoState(eEvent, eState);
        
        if (state == EDK_OK)
        {
            IEE_Event_t eventType = IEE_EmoEngineEventGetType(eEvent);
            IEE_EmoEngineEventGetUserId(eEvent, &userID);
            
            // Log the EmoState if it has been updated
            if (eventType == IEE_UserAdded)
            {
                NSLog(@"User Added");
                IEE_FFTSetWindowingType(userID, IEE_HANN);
                readyToCollect = YES;
            }
            else if (eventType == IEE_UserRemoved)
            {
                NSLog(@"User Removed");
                isConnected = NO;
                readyToCollect = NO;
            }
            else if (eventType == IEE_EmoStateUpdated)
            {
                [self collectFacialData];
            }
        }
        
        if (readyToCollect)
        {
            [self collectBandPowerData];
            [self collectMotionData];
        }
#ifdef IS_THREADED
    }
#endif
}

-(void) collectBandPowerData
{
    if (sendBandPowerData) {
        int nChannels = 5;
        double values[nChannels];
        memset(values, 0, nChannels * sizeof(double));
        
        for(int i = 0 ; i < sizeof(ChannelList)/sizeof(IEE_DataChannel_t) ; ++i)
        {
            NSString *nonStandardChannelName = [non_standard_name_channel objectAtIndex:i];
            
            int result = IEE_GetAverageBandPowers(userID, ChannelList[i], &values[BAND_THETA], &values[BAND_ALPHA], &values[BAND_BETA_LOW], &values[BAND_BETA_HIGH], &values[BAND_GAMMA]);
            
            if(result == EDK_OK){
                [self sendOSCMessage:nonStandardChannelName withValues:values andSize:nChannels];
            }
        }
    }
}

-(void) collectMotionData
{
    if (sendMotionData) {
        IEE_MotionDataUpdateHandle(0, hData);
        
        unsigned int nSamplesTaken = 0;
        IEE_MotionDataGetNumberOfSample(hData,&nSamplesTaken);
        
        if (nSamplesTaken != 0)
        {
            [self collectMotionDataFor:@"Gyro" withDataChannels:gyroChannelList andSamplesTaken:nSamplesTaken];
            [self collectMotionDataFor:@"Accel" withDataChannels:accChannelList andSamplesTaken:nSamplesTaken];
            [self collectMotionDataFor:@"Magn" withDataChannels:magChannelList andSamplesTaken:nSamplesTaken];
        }
    }
}

-(void) collectMotionDataFor : (const NSString *)sensorName withDataChannels : (const IEE_MotionDataChannel_t *)dataChannels andSamplesTaken: (unsigned int)nSamplesTaken
{
    int nDataChannels = 3;
    double values[nDataChannels];
    memset(values, 0, nDataChannels * sizeof(double));
    
    std::unique_ptr<double> ddata(new double[nSamplesTaken]);
    for (int sampleIdx = 0; sampleIdx < (int)nSamplesTaken; ++sampleIdx) {
        for (int i = 0; i < nDataChannels; i++) {
            IEE_MotionDataGet(hData, dataChannels[i], ddata.get(), nSamplesTaken);
            values[i] = ddata.get()[sampleIdx];
        }
        [self sendOSCMessage:sensorName withValues:values andSize:nDataChannels];
    }
}

-(void) collectFacialData
{
    if (sendFacialData) {
        NSString *action;
        double values[2];
        memset(values, 0, 2 * sizeof(double));
        
        IEE_EmoEngineEventGetEmoState(eEvent, eState);
        
        values[0] = IS_FacialExpressionIsBlink(eState) ? 1 : 0;
        [self sendOSCMessage:@"Blink" withValues:values andSize:1];
        
        values[0] = IS_FacialExpressionIsLeftWink(eState) ? 1 : 0;
        [self sendOSCMessage:@"LeftWink" withValues:values andSize:1];
        
        values[0] = IS_FacialExpressionIsRightWink(eState) ? 1 : 0;
        [self sendOSCMessage:@"RightWink" withValues:values andSize:1];
        
        //TODO: ask about facial actions (adapar)
        int upperFaceAction = IS_FacialExpressionGetUpperFaceAction(eState);
        
        switch (upperFaceAction) {
            case FE_SURPRISE:
                action = @"Surprise";
                break;
            case FE_FROWN:
                action = @"Furrow";
                break;
            default:
                action = @"";
        }
        if ([action length] > 0) {
            values[0] = IS_FacialExpressionGetUpperFaceActionPower(eState);
            [self sendOSCMessage:action withValues:values andSize:1];
        }
        
        int lowerFaceAction = IS_FacialExpressionGetLowerFaceAction(eState);
        
        switch (lowerFaceAction) {
            case FE_SMILE:
                action = @"Smile";
                break;
            case FE_CLENCH:
                action = @"Clench";
                break;
            default:
                action = @"";
        }
        if ([action length] > 0) {
            values[0] = IS_FacialExpressionGetLowerFaceActionPower(eState);
            [self sendOSCMessage:action withValues:values andSize:1];
        }
        
        float x;
        float y;
        
        IS_FacialExpressionGetEyeLocation(eState, &x, &y);
        
        values[0] = (double)x;
        values[1] = (double)y;
        [self sendOSCMessage:@"Eye" withValues:values andSize:2];
        
        float left;
        float right;
        
        IS_FacialExpressionGetEyelidState(eState, &left, &right);
        
        values[0] = (double)left;
        values[1] = (double)right;
        
        [self sendOSCMessage:@"EyeLid" withValues:values andSize:2];
    }
}

-(void) sendOSCMessage : (const NSString *)command withValues : (const double [])srcValues andSize : (int)nSrcValues
{
    OSCClient *client = [[OSCClient alloc] init];
    NSString *clientAddress = [NSString stringWithFormat:@"udp://%@:%@", [self.clientIP stringValue], [self.clientPort stringValue]];
    NSMutableArray *values = [[NSMutableArray alloc] initWithCapacity:nSrcValues];

    //TODO: fix field emptying issue with threaded version
    clientAddress = @"udp://127.0.0.1:7000";
    
    for (int i = 0; i < nSrcValues; i++) {
        [values addObject:[NSNumber numberWithDouble:srcValues[i]]];
    }
    
    OSCMessage *message = [OSCMessage to:[NSString stringWithFormat:@"/Insight/%@", command] with:values];
    [client sendMessage:message to:clientAddress];
}

@end
