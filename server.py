# coding=utf-8
import sys
import grpc
from concurrent import futures
import time
import service_pb2
import service_pb2_grpc
import numpy as np
import cv2
import os
import threading
import torch
import asyncio
from multiprocessing import Process
sys.path.append(r'/data')
import subprocess
import threading
import queue


task_running = False


class MyServiceServicer(service_pb2_grpc.MyServiceServicer):
    def __init__(self):
        #self.pid = pid
        self.pid = 0

    def StartPrediect(self, request, context):
        global task_running
        task_running = True
        video_path = request.values
        self.video_path = video_path
        output_queue = queue.Queue()

        def run_subprocess():

            found = False

            process = subprocess.Popen(
                ['/root/miniconda3/bin/python', '-u', '/data/autowiring/video_flowing_case.py', '--video_path',
                 video_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            for line in process.stdout:
                while not task_running:
                    found = True
                    break
                if found:
                    break
                else:
                    print(line.strip(), not task_running)
                    output_queue.put(line.strip())

            process.stdout.close()
            process.kill()
            process.wait()

            stderr_output = process.stderr.read()

            if stderr_output:
                output_queue.put(f"Error: {stderr_output.strip()}")
            output_queue.put(None)

        self.thread = threading.Thread(target=run_subprocess, daemon=True)
        self.thread.start()

        while True:
            try:
                message = output_queue.get(timeout=1)
                if message is None:
                    break
                yield service_pb2.Response(message=message)
            except queue.Empty:
                if context.is_active():
                    continue
                break

    def StopPrediect(self, request, context):
        global task_running
        task_running = False
        print('stop event set', str(task_running))
        # self.thread.join()
        return service_pb2.Response(message="Task cancellation initiated.")

    def ClearData(self, request, context):
        try:
            ClearPath = request.values
            os.remove(ClearPath)
            _, extension = os.path.splitext(ClearPath)
            os.remove(ClearPath.replace(extension, '_prediect.avi'))
        except Exception as e:
            print(e)

        return service_pb2.Response(message="Data Cleansing Complete.")


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10),
                        options=[('grpc.max_send_message_length', -1),  # -1 表示不限制大小
                                 ('grpc.max_receive_message_length', -1)])
    # server = grpc.aio.server(options=[('grpc.max_send_message_length', -1),
    #                                    ('grpc.max_receive_message_length', -1)])
    service_pb2_grpc.add_MyServiceServicer_to_server(MyServiceServicer(), server)
    server.add_insecure_port('[::]:50052')
    server.start()
    server.wait_for_termination()
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

def run_server():
    #pid = os.getpid()
    serve()

if __name__ == '__main__':
    run_server()
