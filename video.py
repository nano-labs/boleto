import objc
import QTKit
from AppKit import *
from Foundation import NSObject
from Foundation import NSTimer
from PyObjCTools import AppHelper
from time import sleep


class NSImageTest(NSObject):
    def init(self):
        self = super(NSImageTest, self).init()
        if self is None:
            return None

        self.session = None
        self.running = True

        return self

    def captureOutput_didOutputVideoFrame_withSampleBuffer_fromConnection_(self, captureOutput, 
                                                                           videoFrame, sampleBuffer, 
                                                                           connection):
        # self.session.stopRunning() # I just want one frame

        # Get a bitmap representation of the frame using CoreImage and Cocoa calls
        ciimage = CIImage.imageWithCVImageBuffer_(videoFrame)
        rep = NSCIImageRep.imageRepWithCIImage_(ciimage)
        bitrep = NSBitmapImageRep.alloc().initWithCIImage_(ciimage)
        bitdata = bitrep.representationUsingType_properties_(NSBMPFileType, objc.NULL)

        import StringIO
        import Image
        from teste import Barcode
        aaa = Image.open(StringIO.StringIO(bitdata.bytes().tobytes()))
        bbb = Barcode(imagem=aaa)
        ddd = bbb.barcode_data()
        if ddd:
            print '##' * 30
            print '##' * 30
            print ddd
            print '##' * 30
            print '##' * 30
            # self.running = False

        # bbb.show_scan()
        # iii.show()
        # aaa.show()
        # import ipdb; ipdb.set_trace()

        # sleep(3)

        # # Save image to disk using Cocoa
        # t0 = time.time()
        # bitdata.writeToFile_atomically_("grab.bmp", False)
        # t1 = time.time()
        # print "Cocoa saved in %.5f seconds" % (t1-t0)

        # Save a read-only buffer of image to disk using Python
        # t0 = time.time()
        # bitbuf = bitdata.bytes()
        # f = open("python.bmp", "w")
        # f.write(bitbuf)
        # f.close()
        # t1 = time.time()
        # print "Python saved buffer in %.5f seconds" % (t1-t0)

        # Save a string-copy of the buffer to disk using Python
        # t0 = time.time()
        # bitbufstr = str(bitbuf)
        # f = open("python2.bmp", "w")
        # f.write(bitbufstr)
        # f.close()
        # t1 = time.time()
        # print "Python saved string in %.5f seconds" % (t1-t0)

        # Will exit on next execution of quitMainLoop_()
        # self.running = False
        # iii.show()


    def quitMainLoop_(self, aTimer):
        # Stop the main loop after one frame is captured.  Call rapidly from timer.
        if not self.running:
            AppHelper.stopEventLoop()

    def startImageCapture(self, aTimer):
        error = None
        print "Finding camera"

        # Create a QT Capture session
        self.session = QTKit.QTCaptureSession.alloc().init()

        # Find iSight device and open it
        dev = QTKit.QTCaptureDevice.defaultInputDeviceWithMediaType_(QTKit.QTMediaTypeVideo)
        print "Device: %s" % dev
        if not dev.open_(error):
            print "Couldn't open capture device."
            return

        # Create an input instance with the device we found and add to session
        input = QTKit.QTCaptureDeviceInput.alloc().initWithDevice_(dev)
        if not self.session.addInput_error_(input, error):
            print "Couldn't add input device."
            return

        # Create an output instance with a delegate for callbacks and add to session
        output = QTKit.QTCaptureDecompressedVideoOutput.alloc().init()
        output.setDelegate_(self)
        if not self.session.addOutput_error_(output, error):
            print "Failed to add output delegate."
            return

        # Start the capture
        print "Initiating capture..."
        self.session.startRunning()


    def main(self):
        # Callback that quits after a frame is captured
        NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(0.1, 
                                                                                 self, 
                                                                                 'quitMainLoop:', 
                                                                                 None, 
                                                                                 True)

        # Turn on the camera and start the capture
        self.startImageCapture(None)

        # Start Cocoa's main event loop
        AppHelper.runConsoleEventLoop(installInterrupt=True)

        print "Frame capture completed."

if __name__ == "__main__":
    test = NSImageTest.alloc().init()
    test.main()