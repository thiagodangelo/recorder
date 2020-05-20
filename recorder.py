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
    parser.add_argument("-dt", "--delta_time", type=float, default=float("inf"))
    parser.add_argument("-res", "--resize_factor", type=float, default=1.0)
    parser.add_argument("-rot", "--rotate", action="store_true")
    parser.add_argument("-rec", "--record", action="store_true")
    parser.add_argument("-rep", "--repeat", action="store_true")
    parser.add_argument("-v", "--view", action="store_true")

    args = parser.parse_args()
    event = Event()
    app = Application(
        sources=args.sources,
        filenames=args.filenames,
        output=args.output,
        event=event,
        delta_time=args.delta_time,
        resize_factor=args.resize_factor,
        rotate=args.rotate,
        record=args.record,
        repeat=args.repeat,
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
    def __init__(self, sources, filenames, output, event, delta_time, resize_factor, rotate, record, repeat, fps, view, api=cv2.CAP_ANY) -> None:
        super().__init__()
        self.sources = sources
        self.filenames = filenames
        self.output = output
        self.event = event
        self.delta_time = delta_time
        self.resize_factor = resize_factor
        self.rotate = rotate
        self.record = record
        self.repeat = repeat
        self.fps = fps
        self.view = view
        self.api = api

    def recorder(self, source, filename):
        def msg_time(msg=""):
            now = datetime.now()
            now_str = now.strftime("%H:%M:%S %d/%m/%Y")
            print(msg, now_str)

        def writer_f(writer: cv2.VideoWriter, writer_event: Event, frames: Queue):
            while not writer_event.is_set() or not frames.empty():
                try:
                    frame = frames.get_nowait()
                    writer.write(frame)
                except:
                    pass
                sleep(0.001)

        def capturer_f(source, filename):
            cap = cv2.VideoCapture(source, self.api)
            writer = None
            writer_event = None
            writer_t = None
            frames = None
            msg_time(msg="Start at: ")
            t0 = time()
            while not self.event.is_set():
                ret, frame = cap.read()
                if not ret or frame is None:
                    msg_time(msg="Error - Stop at: ")
                    if self.repeat:
                        cap = cv2.VideoCapture(source, self.api)
                        msg_time(msg="Error - Start at: ")
                        continue
                    else:
                        break
                if self.resize_factor != 1.0:
                    frame = cv2.resize(frame, None, fx=self.resize_factor, fy=self.resize_factor)
                if self.rotate:
                    frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
                if self.record:
                    if writer is None:
                        h, w, _ = frame.shape
                        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
                        filename = str(self.output / filename)
                        frames = Queue()
                        writer = cv2.VideoWriter(filename, fourcc, self.fps, (w, h), True)
                        writer_event = Event()
                        writer_t = Thread(target=writer_f, args=(writer, writer_event, frames,))
                        writer_t.start()
                    frames.put(frame)
                if self.view:
                    cv2.imshow(filename, frame)
                    key = cv2.waitKey(1)
                    if key == ord('q'):
                        break
                t1 = time()
                dt = t1 - t0
                if dt >= self.delta_time:
                    break
                sleep(0.001)
            msg_time(msg="Stop at: ")
            if self.record:
                msg_time(msg="Waiting to finish video recording at: ")
                writer_event.set()
                writer_t.join()
                writer.release()
                msg_time(msg="Video recording ended at: ")
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
