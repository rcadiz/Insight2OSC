//
//  ViewController.h
//  Insight2OSC
//
//  Created by Cuong Trinh on 11/19/15.
//  Copyright © 2015 Emotiv. All rights reserved.
//

#import <Cocoa/Cocoa.h>
#import <edk/Iedk.h>

@interface ViewController : NSViewController{
    NSArray        *name_channel;
    NSArray        *non_standard_name_channel;
    NSString       *documentDirectory;
}

@property (weak) IBOutlet NSImageView *electrodeStatusImageAF3;
@property (weak) IBOutlet NSImageView *electrodeStatusImageT7;
@property (weak) IBOutlet NSImageView *electrodeStatusImageT8;
@property (weak) IBOutlet NSImageView *electrodeStatusImagePz;
@property (weak) IBOutlet NSImageView *electrodeStatusImageAF4;

@property (weak) IBOutlet NSTextField *electrodeLabelAF3;
@property (weak) IBOutlet NSTextField *electrodeLabelAF4;
@property (weak) IBOutlet NSTextField *electrodeLabelT7;
@property (weak) IBOutlet NSTextField *electrodeLabelT8;
@property (weak) IBOutlet NSTextField *electrodeLabelPz;

@property (weak) IBOutlet NSTextField *clientIP;
@property (weak) IBOutlet NSTextField *clientPort;


@end

