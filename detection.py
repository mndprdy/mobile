import os.path
import subprocess
import boto3
import requests
import json

sqs = boto3.client('sqs')

queue_name = 'sqslistener01'

response = sqs.get_queue_url(QueueName=queue_name)
queue_url = response['QueueUrl']
video_extensions = ['mp4', 'webm','mp3']

def video_file(url):
    return  ''.join(url.split('?')[:-1]).split('.')[-1] in video_extensions

while True:

    response = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=10,
        WaitTimeSeconds=20
    )

    messages = response.get('Messages', [])
    if messages:
        for message in messages:
            print('Received message:', message['Body'])
            data = message['Body']
            data = json.loads(data)

            if 's3_file_url' in data:
                file_url = data['s3_file_url']

                if video_file(file_url):
                    response = requests.get(file_url)
                    if response.status_code == 200:
                        file_name = ''.join(file_url.split('?')[:-1]).split('/')[-1]
                        with open(file_name, 'wb') as file:
                            file.write(response.content)
                        print(f'Successfully downloaded file: {file_name}')
                        # Set up the detector
                        source = os.path.join("/home/mani/Flask_project/Sqs_consumer", file_name)
                        print(f'path:{source}')
                        detector_cmd = ["python3", "detect_3.py", "--weights", "best.pt", "--conf", "0.5", "--source", file_name]
                        # detector_cmd = f'python3 detect.py --weights best.pt --conf 0.5 --source {source}'
                        detector_process = subprocess.Popen(detector_cmd)

                    else:
                        print(f'Failed to download file: {file_url}')
                else:
                    print(f'Skipping file with unsupported extension: {file_url}')
            else:
                print('Message does not contain "s3_file_url" key.')

            sqs.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=message['ReceiptHandle']
            )
    else:
        print('No messages received.')
