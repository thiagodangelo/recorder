# coding: utf-8

import argparse
import pathlib
import cv2

from datetime import datetime
from time import sleep, time
from threading import Thread, Event
from queue import Queue


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="Video Recorder",
        description="Multi input and output video recorder",
    )
    parser.add_argument("-s", "--sources", type=str, nargs='+', default=['0'])
    parser.add_argument("-f", "--filenames", type=str, nargs='+', default=['video.avi'])
    parser.add_argument("-o", "--output", type=pathlib.Path, default='./')
    parser.add_argument("-fps", "--fps", type=int, default=30)
    parser.add_argument("-res", "--resize_factor", type=float, default=1.0)
    parser.add_argument("-rot", "--rotate", action="store_true")
    parser.add_argument("-rec", "--record", action="store_true")
    parser.add_argument("-v", "--view", action="store_true")

    args = parser.parse_args()
    event = Event()
    app = Application(
        sources=args.sources,  
        filenames=args.filenames, 
        output=args.output, 
        event=event, 
        resize_factor=args.resize_factor, 
        rotate=args.rotate, 
        record=args.record, 
        fps=args.fps, 
        view=args.view,
    )
    app.start()
    while not event.is_set():
        try:
            sleep(1.0)
        except KeyboardInterrupt:
            event.set()


class Application(Thread):
    def __init__(self, sources, filenames, output, event, resize_factor, rotate, record, fps, view) -> None:
        super().__init__()
        self.sources = sources
        self.filenames = filenames
        self.output = output
        self.event = event
        self.resize_factor = resize_factor
        self.rotate = rotate
        self.record = record
        self.fps = fps
        self.view = view

    def recorder(self, source, filename):
        frames = Queue()

        def msg_time(msg=""):
            now = datetime.now()
            now_str = now.strftime("%H:%M:%S %d/%m/%Y")
            print(msg, now_str)

        def writer_f(writer: cv2.VideoWriter):
            while not self.event.is_set() or not frames.empty():
                frame = frames.get()
                writer.write(frame)
                sleep(0.01)

        def capturer_f(source, filename):
            cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
            writer = None
            writer_t = None
            msg_time(msg="Start at: ")
            while not self.event.is_set():
                ret, frame = cap.read()
                if not ret or frame is None:
                    msg_time(msg="Error - Stop at: ")
                    cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
                    msg_time(msg="Error - Start at: ")
                    continue
                if self.resize_factor != 1.0:
                    frame = cv2.resize(frame, None, fx=self.resize_factor, fy=self.resize_factor)
                if self.rotate:
                    frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
                if self.record:
                    if writer is None:
                        h, w, _ = frame.shape
                        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
                        filename = str(self.output / filename)
                        writer = cv2.VideoWriter(filename, fourcc, self.fps, (w, h), True)
                        writer_t = Thread(target=writer_f, args=(writer,))
                        writer_t.start()
                    frames.put(frame)
                if self.view:
                    cv2.imshow(filename, frame)
                    key = cv2.waitKey(1)
                    if key == ord('q'):
                        break
                sleep(0.01)
            msg_time(msg="Stop at: ")
            if self.record:
                writer_t.join()
                writer.release()
            if self.view:
                cv2.destroyWindow(filename)
        
        return Thread(target=capturer_f, args=(source, filename)) 

    def run(self) -> None:
        def str_or_int(string):
            try:
                return int(string)
            except:
                return string

        threads = []
        for source, filename in zip(self.sources, self.filenames):
             threads.append(self.recorder(source=str_or_int(source), filename=filename))
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.event.set()


if __name__ == "__main__":
    main()
