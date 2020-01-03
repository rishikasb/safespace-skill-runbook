# mansplaining-skill


#Instructions

1. Deploy the "Gender Classifier" model from AWS Marketplace

1.1 Visit https://aws.amazon.com/marketplace/ and search for "Gender Classifier"

1.2 Select "Gender Classifier" from Figure 8, the CPU version. Continue to subscribe. Review the pricing information and  Click - "Accept offer”

1.3 You will see a message “Thank you for subscribing.  You can now use your product”. 

1.4 Click “Continue to configuration”. Choose Software version : 1; Region : us-west-2. Click “View in SageMaker”

1.5 In the SageMaker Model packages under the “AWS Marketplace subscriptions" you will see this model show up.

1.6 Select the model. Create Model.

1.7 For Model Settings :
    
1.7.1 Name : Mansplaining-Gender-Classifier
    
1.7.2 IAM Role. : Create Role, that has access to any s3 bucket

1.7.3 Container definition : Select Use a model package subscription from AWS Marketplace

1.8 From models screen, select the model created.

1.8.1 Click Create endpoint

1.8.2 Create and configure endpoint

1.8.3 Enter Name : Mansplaining-Gender-Classifier-Endpoint

1.8.4 Select “Create a new endpoint configuration”

2.Launch a cloudformation stack using the file "MansplainingResources.yml"

2.1.Verify the resources created : S3 bucket

2.3 In the S3 bucket, create a folder "lambda-code" and upload two zip files from this repo.

2.3.1 lambda-code/AnalyzeMeetingLambda.zip and lambda-code/TranscribeLambda.zip

3.Launch a cloudformation stack using the file "Mansplaining_LambdaFunctions.yml"

3.1.Verify the two lambda functions created.

4.Configure Transcribe Lambda trigger through console (Note : this portiona can also be automated based on instructions at https://aws.amazon.com/premiumsupport/knowledge-center/cloudformation-s3-notification-lambda/ )

4.1 Click on the lambda function name

4.2 Add trigger

4.3 Select a trigger.  Choose S3

4.4 Bucket : Select the mansplaining bucket.

4.5 Event type : PUT

4.6 Prefix : meeting-recordings/

4.7 Suffix : Leave empty

4.8 Click Add

5.Configure AnalyzeMeeting Lambda trigger through console (Note : this portiona can also be automated based on instructions at https://aws.amazon.com/premiumsupport/knowledge-center/cloudformation-s3-notification-lambda/ )

5.1 Click on the lambda function name

5.2 Add trigger

5.3 Select a trigger.  Choose S3

5.4 Bucket : Select the mansplaining bucket.

5.5 Event type : COPY

5.6 Prefix : meeting-transcriptions/

5.7 Suffix : Leave empty

5.8 Click Add

6.Upload meeting recordings to mansplaining bucket

6.1 If not already created, create a folder "meeting-recordings" in the bucket

6.2 Upload the meeting recording to the "meeting-recordings" folder.

6.3 This will automatically trigger "TranscribeLambda" which transcribes the recording and stores in the folder "meeting-transcriptions"

6.4 Once the meeting transcription is created, "AnalyzeMeetingLambda" is triggered.
