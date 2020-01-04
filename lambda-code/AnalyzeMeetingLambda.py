import json
import boto3
import time
import base64
import os

s3_resource = boto3.resource('s3')
elastictranscoder_client = boto3.client('elastictranscoder')
s3_client = boto3.client('s3')
sagemaker_client = boto3.client('sagemaker-runtime')

dynamodb_client = boto3.client('dynamodb')

def lambda_handler(event, context):
    # Get the filename(key) that caused the event.
    record = event["Records"][0]
    region = record["awsRegion"]
    bucket = record["s3"]["bucket"]["name"]
    key = record["s3"]["object"]["key"]
    print("key is ", key)

    #Get the content of the file
    obj = s3_resource.Object(bucket, key)
    body = obj.get()["Body"].read()
    json_content = json.loads(body)

    #Get the transcription results
    transcription_results = json_content["results"]

    #Get the speaker times from the transcript
    times = []
    for segment in transcription_results["speaker_labels"]["segments"]:
       start_time = float(segment["start_time"])
       end_time = float(segment["end_time"])

       # get a 1/2 second snippet after each speaker starts
       delta = .5

       times.append((start_time, delta))

    print("Speaker times ")
    print(times)

    ##Form the inputs to elastic transcoder.
    inputs = []
    for start_time, duration in times:
       json_obj = {
           "Key": "meeting-recordings/Border Security Part1.m4a",
           "TimeSpan": {
               "StartTime": str(start_time),
               "Duration": str(duration)
           }
       }
       inputs.append(json_obj)
    print("Number of inputs ", len(inputs))
    print(inputs)

    ##Form the outputs to elastic transcoder.
    outputs = []
    for idx in range(len(times)):
       json_obj = {
           "Key": "micro_clip_{}.wav".format(idx),
           # configure this by looking at the console based on the type of audio file you want
           "PresetId":"1351620000001-300300"
       }
       outputs.append(json_obj)
    print("Number of outputs ", len(outputs))
    print(outputs)

    pipeline = elastictranscoder_client.create_pipeline(
       Name="mansplaining_pipeline",
       InputBucket=bucket,
       OutputBucket=bucket,
       Role="arn:aws:iam::923611210851:role/service-role/AmazonSageMaker-ExecutionRole-20191229T181432")

    pipeline_id = pipeline["Pipeline"]["Id"]
    print(" Pipeline ID is ", pipeline_id)

    create_job_responses = []
    transcoder_jobs = []

    #need to loop through batches of 30  (TODO : make this configurable)'
    iterator = round(len(inputs)/5)
    for i in range(iterator):
     print(i)
     lb = i * 5
     up = lb + 5
     if up > len(inputs):
       up = len(inputs)
     create_job_response = elastictranscoder_client.create_job(
        PipelineId=pipeline_id,
        Inputs=inputs[lb:up],
        Outputs = outputs[lb:up] )
     print("create_job_response ", create_job_response)
     create_job_responses.append(create_job_response)
     job_id = create_job_response["Job"]["Id"]
     transcoder_jobs.append(job_id)

    #Wait for the jobs to be completed.
    print("Elastic Transcoder Jobs: ", transcoder_jobs )
    for job in transcoder_jobs:
     while True:
       response = elastictranscoder_client.read_job(
         Id=job
       )
       job_status = response["Job"]["Output"]["Status"]
       print("******* job_id ", job, " status is ", job_status)
       if job_status in ["Complete", "Failed"]:
         break;

    #Now convert WAV to byte64 encoded and make predictions
    male_count = 0
    female_count = 0

    for create_job_response in create_job_responses:
     transcoder_ouputs = create_job_response["Job"]["Outputs"]
     print("transcoder outputs ", transcoder_ouputs)
     for transcoder_output in transcoder_ouputs:
       transcoder_output_key = transcoder_output["Key"]

       print("transcoder_output_key ", transcoder_output_key)

       s3_client.download_file(bucket, transcoder_output_key, "/tmp/"+ transcoder_output_key)

       with open("/tmp/"+ transcoder_output_key, "rb") as wav_file:
         file_contents = wav_file.read()
         wav_file.close()
         encoded_file_contents=base64.b64encode(file_contents).decode("utf-8")
         print("encoded_file_contents ", encoded_file_contents)

       payload = "{" + "\"instances\": [{" + "\"audio\": {" + "\"b64\": \"" + encoded_file_contents + "\"}}]}"

       response = sagemaker_client.invoke_endpoint(
           EndpointName="Mansplaining-Gender-Classifier-EP",
           Body=payload.encode("utf-8"),
           ContentType="application/json"
       )

       prediction_for_wav_part = response["Body"].read().decode("utf-8")
       print("prediction for part wav file is ", prediction_for_wav_part)

       prediction_for_wav_part_json = json.loads(prediction_for_wav_part)

       predicted_label = prediction_for_wav_part_json["predictions"][0]["label"]

       print("predicted_label ", predicted_label)

       if "female" in predicted_label:
         female_count += 1
       else:
         male_count += 1

       #predictions_for_wav_parts.append(prediction_for_wav_part)

    #Combine the predictions of individual wav parts
    percent_male = 100 * male_count / (male_count + female_count)
    percent_female = 100 * female_count / (male_count + female_count)

    meeting_analysis = "Percentage of time men were speaking was {}%, while for women it was {}%.".format(percent_male, percent_female)

    print(meeting_analysis)

    table = os.environ['MansplainingDynamoDB']

    dynamodb_client.put_item(
        TableName=table,
        Item={
            'meeting-id': {'S': key},
            'analysis': {'S': meeting_analysis}
        }
    )

    #dynamodb.put_item(TableName='fruitSalad', Item={'fruitName': {'S': 'Banana'}, 'key2': {'N': 'value2'}})

    #print ("Percentage of time men were speaking was {}%, while for women it was {}%.".format(percent_male, percent_female))

    return "Completed transcribing the meeting recording"
