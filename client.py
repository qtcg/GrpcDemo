import grpc
import service_pb2
import service_pb2_grpc
import numpy as np
import time
import shutil
import os
import json
import asyncio
import threading

task_running = True

def DataPreparation(videopath, ServeConfig):
    try:
        bashname = os.path.basename(videopath)
    except:
        bashname = videopath.split('/')[-1]
    os.makedirs(ServeConfig['ClientWorkPath'] ,exist_ok=True)
    print(os.path.join(ServeConfig['ClientWorkPath'], bashname))
    if not os.path.exists(os.path.join(ServeConfig['ClientWorkPath'], bashname)):
        shutil.copy2(videopath, os.path.join(ServeConfig['ClientWorkPath'], bashname))

    return ServeConfig['ServeWorkPath'] + '/' + bashname


def DataPostProcessing(videodict, ServeConfig):
    videopath = videodict['video']
    try:
        bashname = os.path.basename(videopath)
        bashname = bashname.split('.')[0] + '_prediect.avi'
    except:
        bashname = videopath.split('/')[-1]
        bashname = os.path.join(bashname.split('.')[0], '_prediect.avi')

    shutil.copy2(os.path.join(ServeConfig['ClientWorkPath'], bashname), videopath.split('.')[0] + '_prediect.avi')


def stop_request(stub, ui):
    global task_running
    while task_running:
        pass

    request = service_pb2.Request(values='stop')
    response = stub.StopPrediect(request)

    if ui:
        ui.printf(response.message)
    else:
        print(response.message)


def run(videodict, ui=None):

    global task_running
    task_running=True
    videopath = videodict['video']
    with open('Serve.json', 'r') as json_file:
        ServeConfig = json.load(json_file)

    with grpc.insecure_channel('localhost:50052',
                                options=[('grpc.max_send_message_length', -1),
                                         ('grpc.max_receive_message_length', -1)]) as channel:
        stub = service_pb2_grpc.MyServiceStub(channel)

        videopath = DataPreparation(videopath, ServeConfig)

        threading.Thread(target=stop_request, args=(stub, ui)).start()
        if ui:
            ui.printf('Send {} to Server'.format(videopath))
        else:
            print(print('Get Result from Server'))
        request = service_pb2.Request(values=videopath)
        if ui:
            ui.printf('Get Result from Server')
        else:
            print('Get Result from Server')

        try:
            response_stream = stub.StartPrediect(request)
        except grpc.RpcError as e:
            print(f"RPC错误: {e.code()}, {e.details()}")
        except asyncio.TimeoutError:
            print("请求超时，未能获得响应")

        for response in response_stream:
            if ui:
                ui.printf("Output from server:{}" .format(response.message))
            else:
                print("Output from server:", response.message)
        try:
            DataPostProcessing(videodict, ServeConfig)
        except Exception as e:
            print(e)

        try:
            response_Clear = stub.ClearData(request)
        except grpc.RpcError as e:
            print(f"RPC错误: {e.code()}, {e.details()}")
        except asyncio.TimeoutError:
            print("请求超时，未能获得响应")

        if ui:
            ui.printf(response_Clear.message)
        else:
            print(response_Clear.message)


def StopRun():
    global task_running
    task_running = False


if __name__ == '__main__':
     run('F:\\1')
