import json

if __name__ == '__main__':
    data = {
        "ServeWorkPath": "/data/workspace/video",
        "ClientWorkPath": r'D:\linux_data\workspace\video',
    }
    with open('Serve.json', 'w') as json_file:
        json.dump(data, json_file, indent=4)
