# SafeSpace Alexa Skill

End-to-End Workflow: General Overview & Serviced Used

- Deploy Chime meeting recording application:
    - Services used: Cloud9, ECR & ECR (Docker image), networking resources (VPC, security groups, subnets), auto-scaling group for ECS cluster, IAM roles
    - General overview: 
        - Create repository in ECR, build and upload docker image into ECR
        - Deploy.js script (obtained from amazon-chime-sdk-recording-demo GitHub repository) which creates CloudFormation Stack and sets up the recording service
        - Start the Chime meeting and participants can join: meeting URL created from a second deploy.js script (obtained from amazon-chime-sdk-js GitHub repository), which creates CloudFormation Stack, Lambda function, API Gateway resources
        - Start & stop the recording: invoke REST API in API Gateway by utilizing Postman, set up proper AWS account authentication and start/stop meeting recording by sending two separate POST requests.
        - Finally, the successful meeting recording is uploaded to a pre-designated S3 bucket, which connects us to the rest of the analysis steps of the workflow.
        
- Meeting recording file in S3: copy file to appropriate bucket
    - Service used: Lambda function
    - General overview: Copy recording file to the appropriate S3 bucket, which has already been designated to serve as the trigger for the rest of the analysis workflow. This achieved by a single Lambda function and utilizes a trigger. 
    
- Transcribe, transcode, and analyze the recording:
    - Services used: Lambda, Transcribe, Elastic Transcoder, Sagemaker (Marketplace model)
    - General overview: TranscribeLambda function utilizes the Transcribe service to convert speech to text. The output of this function is a .json file, uploaded to a separate sub-directory of the S3 bucket. Once this file is uploaded, the next function is triggered -- the AnalyzeMeetingLambda function. This comprises of two steps: transcoding and the audio gender classifier model. Elastic Transcoder is used to convert the encoding format of the recording file to base64, as this is the required input to the machine learning model. Then, we run the Audio Gender Classifier model in Sagemaker through a batch transform process. The final output is %men vs. %women speaking for the duration of the meeting, indicating the analysis is complete.

- Load and store the completed analysis:
    - Service used: DynamoDB
    - General overview: The new analysis item is loaded into the DynamoDB table. Each new table entry contains the following information: the "fact number", which is how we have specified each value in the Alexa skill, the analysis itself (%men vs. %women speaking), the meeting-id (which is the entire filepath from S3), and the meeting-category (which is a sub-directory in the S3 bucket and can be pre-defined by the user). 

- Alexa Skill: query for analysis of latest meeting
    - Service used: Alexa Skills Kit, Alexa Developer Console
    - General overview: The skill is invoked in the developer console, but can also be invoked in any Echo device. The skill is invoked by the user saying "open SafeSpace skill", at which point we have entered the skill. Next, the user says a simple command, "analyze my meeting", which returns a two-part speech output: the number of meetings that have already been analyzed, along with the new analysis item, which is specified by its meeting category and the gender classification output itself. 
    
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

2.1 Access CloudFormation through the AWS Console

2.1.1 Select "create stack" and choose the "with new resources" option

2.1.2 Default option for "Prerequisite - prepare template" should be "template is ready" - do not change this. Select "upload a template file" under the "Specify template" option and now upload the "MansplainingResources.yml" here.

2.1.3 Click "Next", no other options need to be changed, except use your own initials for the uniqueID (note: this must be at least 3 characters long).

2.2 Verify the resources created : S3 bucket

2.3 In the S3 bucket, create a folder "lambda-code" and upload three zip files from this repo.

2.3.1 lambda-code/AnalyzeMeetingLambda.zip, lambda-code/TranscribeLambda.zip, and lambda-code/AlexaSkillLambda.zip

3. Launch a cloudformation stack using the file "Mansplaining_LambdaFunctions.yml". Follow the same steps as above in 2.1.1-2.1.3. 

3.1.Verify the two lambda functions created.

4.Configure Transcribe Lambda trigger through console (Note : this portiona can also be automated based on instructions at https://aws.amazon.com/premiumsupport/knowledge-center/cloudformation-s3-notification-lambda/ )

4.1 Click on the lambda function name

4.2 Add trigger (note: You can't create triggers for the $LATEST version, you must create them for a numbered version, as explained here: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/lambda-edge-add-triggers-lam-console.html)

4.3 Select a trigger.  Choose S3

4.4 Bucket : Select the mansplaining bucket.

4.5 Event type : PUT

4.6 Prefix : meeting-recordings/

4.7 Suffix : Leave empty

4.8 Click Add

5.Configure AnalyzeMeeting Lambda trigger through console (Note : this portiona can also be automated based on instructions at https://aws.amazon.com/premiumsupport/knowledge-center/cloudformation-s3-notification-lambda/ )

5.1 Click on the lambda function name

5.2 Add trigger (note: You can't create triggers for the $LATEST version, you must create them for a numbered version, as explained here: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/lambda-edge-add-triggers-lam-console.html)

5.3 Select a trigger.  Choose S3

5.4 Bucket : Select the mansplaining bucket.

5.5 Event type : COPY

5.6 Prefix : meeting-transcriptions/

5.7 Suffix : Leave empty

5.8 Click Add

6. Configure AlexaSkillLambda trigger through console (Note : this portiona can also be automated based on instructions at https://aws.amazon.com/premiumsupport/knowledge-center/cloudformation-s3-notification-lambda/ )

6.1 Click on the lambda function name

6.2 Add trigger (note: You can't create triggers for the $LATEST version, you must create them for a numbered version, as explained here: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/lambda-edge-add-triggers-lam-console.html)

6.3 Select a trigger.  Choose AlexaSkill

6.4 Enter the Alexa skill id collected from the Alexa developer portal.

7.Upload meeting recordings to mansplaining bucket

7.1 If not already created, create a folder "meeting-recordings" in the bucket

7.2 Upload the meeting recording to the "meeting-recordings" folder.  (Note : Make sure that there are no spaces in the filename)

7.3 This will automatically trigger "TranscribeLambda" which transcribes the recording and stores in the folder "meeting-transcriptions"

7.4 Once the meeting transcription is created, "AnalyzeMeetingLambda" is triggered.
