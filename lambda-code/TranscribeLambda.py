import json
import boto3
import time

transcribe = boto3.client('transcribe')
s3_resource = boto3.resource('s3')

def lambda_handler(event,context):
    print("event is: %", event)
    record = event["Records"][0]
    #print("Record is ", record)
    region = record["awsRegion"]
    #print("region is ", region)
    bucket = record["s3"]["bucket"]["name"]
    #print("bucket is ", bucket)
    key = record["s3"]["object"]["key"]
    print("key is ", key)

    job_uri = "https://" + bucket + ".s3-" + region + ".amazonaws.com/" + key
    print("job_uri ", job_uri)

    ##Start the transcription job
    timestamp = time.strftime("-%Y-%m-%d-%H-%M-%S", time.gmtime())

    # key is of the form 'meeting-recordings/cateogry/filename.mp4'.
    # Use the filename.mp4 in the job_name
    # Use meeting category as prefix for the output
    meeting_category = key.split("/")[1]
    job_name = key.split("/")[2] + "-" + timestamp

    transcribe.start_transcription_job(
      TranscriptionJobName=job_name,
      Media={"MediaFileUri": job_uri},
      MediaFormat="mp4",
      LanguageCode="en-US",
      OutputBucketName=bucket,
      Settings= {
        "ShowSpeakerLabels": True,
        "MaxSpeakerLabels":10
      }
    )

    while True:
        status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
        if status["TranscriptionJob"]["TranscriptionJobStatus"] in ["COMPLETED", "FAILED"]:
            break
        print("Transcribe Job Running...")
        time.sleep(5)

    print(status)
    #print("######")
    transcribed_meeting = status["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
    transcribed_meeting_keys = transcribed_meeting.split("/")
    transcribed_meeting_key = transcribed_meeting_keys[-1]

    print("transcribed_meeting_key ", transcribed_meeting_key)

    # Copy the transcribed meeting to Output folder
    copy_source = {
        "Bucket": bucket,
        "Key": transcribed_meeting_key
    }

    s3_resource.meta.client.copy(copy_source, Bucket=bucket,
                                 Key="meeting-transcriptions/" + meeting_category + "/" + transcribed_meeting_key)

    # Delete the original transcribed meeting
    s3_resource.Object(bucket, transcribed_meeting_key).delete()

    return "Completed transcribing the meeting recording"