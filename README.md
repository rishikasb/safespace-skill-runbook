# mansplaining-skill


#Instructions

1. Launch a cloudformation stack using the file "MansplainingResources.yml"

2. Verify the resources

3. Configure Transcribe Lambda trigger through console (Note : this portiona can also be automated based on instructions at https://aws.amazon.com/premiumsupport/knowledge-center/cloudformation-s3-notification-lambda/ )
3.1 Click on the lambda function name
3.2 Add trigger
3.3 Select a trigger.  Choose S3
3.4 Bucket : Select the mansplaining bucket.
3.5 Event type : PUT
3.6 Prefix : meeting-recordings/
3.7 Suffix : Leave empty
3.8 Click Add

4. Configure AnalyzeMeeting Lambda trigger through console (Note : this portiona can also be automated based on instructions at https://aws.amazon.com/premiumsupport/knowledge-center/cloudformation-s3-notification-lambda/ )
4.1 Click on the lambda function name
4.2 Add trigger
4.3 Select a trigger.  Choose S3
4.4 Bucket : Select the mansplaining bucket.
4.5 Event type : COPY
4.6 Prefix : meeting-transcriptions/
4.7 Suffix : Leave empty
4.8 Click Add

5. Upload meeting recordings to mansplaining bucket
5.1 If not already created, create a folder "meeting-recordings" in the bucket
5.2 Upload the meeting recording to the "meeting-recordings" folder.
5.3 This will automatically trigger "TranscribeLambda" which transcribes the recording and stores in the folder "meeting-transcriptions"
5.4 Once the meeting transcription is created, "AnalyzeMeetingLambda" is triggered.
5.5  