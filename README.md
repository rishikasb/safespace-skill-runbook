# SafeSpace Alexa Skill

This summer internship project's goal is to enhance an existing Alexa skill (Mansplaining Skill). and extend functionalities, involving leveraging additional AWS services and integration with the Chime SDK. The SafeSpace skill is an innovative solution that leverages Alexa and SageMaker (Marketplace ML models) to highlight the importance of gender equality in conversations and discussions, particularly for professional meetings with women and men. It analyzes meeting recordings (audio-only analysis) by providing the distribution of speaking time between men and women. This gives insight into the nature of the meeting discussion, and speaks to the inclusivity of women in the STEM field. 

![Architecture Diagram](https://github.com/rishikasb/safespace-skill-runbook/blob/master/SafeSpace%20Skill%20-%20Architecture%20Diagram%20(1).png)

## End-to-End Workflow: General Overview & Services Used

- **Deploy Chime meeting recording application**:
    - Services used: Cloud9, ECR & ECR (Docker image), networking resources (VPC, security groups, subnets), auto-scaling group for ECS cluster, IAM roles
    - General overview: 
        - Create repository in ECR, build and upload docker image into ECR
        - Deploy.js script (obtained from amazon-chime-sdk-recording-demo GitHub repository) which creates CloudFormation Stack and sets up the recording service
        - Start the Chime meeting and participants can join: meeting URL created from a second deploy.js script (obtained from amazon-chime-sdk-js GitHub repository), which creates CloudFormation Stack, Lambda function, API Gateway resources
        - Start & stop the recording: invoke REST API in API Gateway by utilizing Postman, set up proper AWS account authentication and start/stop meeting recording by sending two separate POST requests.
        - Finally, the successful meeting recording is uploaded to a pre-designated S3 bucket, which connects us to the rest of the analysis steps of the workflow.
        
- **Meeting recording file in S3: copy file to appropriate bucket**
    - Service used: Lambda function
    - General overview: Copy recording file to the appropriate S3 bucket, which has already been designated to serve as the trigger for the rest of the analysis workflow. This achieved by a single Lambda function and utilizes a trigger. 
    
- **Transcribe, transcode, and analyze the recording**:
    - Services used: Lambda, Transcribe, Elastic Transcoder, Sagemaker (Marketplace model)
    - General overview: TranscribeLambda function utilizes the Transcribe service to convert speech to text. The output of this function is a .json file, uploaded to a separate sub-directory of the S3 bucket. Once this file is uploaded, the next function is triggered -- the AnalyzeMeetingLambda function. This comprises of two steps: transcoding and the audio gender classifier model. Elastic Transcoder is used to convert the encoding format of the recording file to base64, as this is the required input to the machine learning model. Then, we run the Audio Gender Classifier model in Sagemaker through a batch transform process. The final output is %men vs. %women speaking for the duration of the meeting, indicating the analysis is complete.

- **Load and store the completed analysis**:
    - Service used: DynamoDB
    - General overview: The new analysis item is loaded into the DynamoDB table. Each new table entry contains the following information: the "fact number", which is how we have specified each value in the Alexa skill, the analysis itself (%men vs. %women speaking), the meeting-id (which is the entire filepath from S3), and the meeting-category (which is a sub-directory in the S3 bucket and can be pre-defined by the user). 

- **Alexa Skill: query for analysis of latest meeting**
    - Service used: Alexa Skills Kit, Alexa Developer Console
    - General overview: The skill is invoked in the developer console, but can also be invoked in any Echo device. The skill is invoked by the user saying "open SafeSpace skill", at which point we have entered the skill. Next, the user says a simple command, "analyze my meeting", which returns a two-part speech output: the number of meetings that have already been analyzed, along with the new analysis item, which is specified by its meeting category and the gender classification output itself. 
    
## Instructions

1. Deploy the "Gender Classifier" model from AWS Marketplace

    * 1.1 Visit https://aws.amazon.com/marketplace/ and search for "Gender Classifier"

    * 1.2 Select "Audio Gender Classifier" from Figure Eight, the CPU version. Click "Continue to subscribe". 

    * 1.3 Review the pricing information: ensure the field demonstration offer option is selected from the dropdown menu. 

    * 1.4 Click "Accept Offer”, and you will see a message: “Thank you for subscribing.  You can now use your product”. 

    * 1.5 Click “Continue to configuration”: You will now be at a page "Configure and launch".
        * 1.5.1 For "select your launch method", select "SageMaker console".
        * 1.5.2 For "configure your Amazon SageMaker console): choose Software version : 1 and Region : us-west-2.
        * 1.5.3 Select "Create a real-time inference endpoint", then click "View in Amazon Sagemaker". 

    * 1.6 You will now arrive in SageMaker in the AWS console and should be inside the appropriate model subscription for the Audio Gender Classifier Marketplace model.

    * 1.7 For "Model Settings" :
        * 1.7.1 Model Name : Mansplaining-Gender-Classifier
        * 1.7.2 IAM Role. : Create a new role: "S3 buckets you specify - Any S3 bucket", then click "Create role". 
        * 1.7.3 Container definition 1: Select "Use a model package subscription from AWS Marketplace"
        * 1.7.4 Click "Next". 

    * 1.8 You will now arrive at the screen "Create endpoint". 
        * 1.8.1 Name : Mansplaining-Gender-Classifier-Endpoint
        * 1.8.2 Select “Create a new endpoint configuration”
        * 1.8.3 For "New endpoint configuration": select default Endpoint configuration name, No Custom Encryption, and click "Create endpoint configuration". 

2. Launch a Cloudformation Stack using the file "MansplainingResources.yml"
    
    * 2.1 Access CloudFormation through the AWS Console
        * 2.1.1 Select "create stack" and choose the "with new resources" option
        * 2.1.2 Default option for "Prerequisite - prepare template" should be "template is ready" - do not change this. Select "upload a template file" under the "Specify template" option and now upload the "MansplainingResources.yml" here.
        * 2.1.3 Click "Next", no other options need to be changed, except use your own initials for the uniqueID (note: this must be at least 3 characters long).
        * 2.1.4 Verify the resources created, specifically in the S3 bucket.

    * 2.2 In the S3 bucket, create a folder "lambda-code" and upload four zip files from this repo.
        * 2.3.1 lambda-code/AnalyzeMeetingLambda.zip, lambda-code/TranscribeLambda.zip, lambda-code/AlexaSkillLambda.zip, and lambda-code/copyrecording.zip.

3. Launch a CloudFormation Stack using the file "Mansplaining_LambdaFunctions.yml". Follow the same steps as above in 2.1.1-2.1.4. 

    * 3.1.Verify all four Lambda functions are created.

4. Configure TranscribeLambda trigger through console (Note: this portion can also be automated based on instructions at https://aws.amazon.com/premiumsupport/knowledge-center/cloudformation-s3-notification-lambda/)

    * 4.1 Click on the Lambda function name
    
    * 4.2 Add trigger (note: You can't create triggers for the $LATEST version, you must create them for a numbered version, as explained here: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/lambda-edge-add-triggers-lam-console.html)
    
    * 4.3 Select a trigger:
        * 5.3.1 Choose S3
        * 5.3.2 Bucket : Select the mansplaining bucket.
        * 5.3.3 Event type : PUT
        * 5.3.4 Prefix : meeting-recordings/
        * 5.3.5 Suffix : Leave empty
        * 5.3.5 Click "Add"

5. Configure AnalyzeMeetingLambda trigger through console (Note : this portion can also be automated based on instructions at https://aws.amazon.com/premiumsupport/knowledge-center/cloudformation-s3-notification-lambda/)

    * 5.1 Click on the Lambda function name
    
    * 5.2 Add trigger (note: You can't create triggers for the $LATEST version, you must create them for a numbered version, as explained here: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/lambda-edge-add-triggers-lam-console.html)
    
    * 5.3 Select a trigger.  Choose S3
        * 5.3.1 Bucket : Select the mansplaining bucket.
        * 5.3.2 Event type : COPY
        * 5.3.3 Prefix : meeting-transcriptions/
        * 5.3.4 Suffix : Leave empty
        * 5.3.5 Click "Add"

6. Create/configure SafeSpace Alexa Skill and configure AlexaSkillLambda and its trigger through the console (Note : this portion can also be automated based on instructions at https://aws.amazon.com/premiumsupport/knowledge-center/cloudformation-s3-notification-lambda/)
    
    * 6.1 Configure the Alexa Skill.
        * 6.1.1 Navigate to https://developer.amazon.com/alexa/console/askClick and click ‘Create Skill”
        * 6.1.2 Skill name : SafeSpace
        * 6.1.3 Default language : English (US)
        * 6.1.4 Choose a model to add to your skill
            * 6.1.4.1 Click “Custom”
            * 6.1.4.2 Choose a method to host your skill’s backend resources, and click “Alexa-Hosted(Python)”
            * 6.1.4.3 Click “Create Skill”
        * 6.1.5 On the next page, choose a template to add to your skill:
            * 6.1.5.1 Click “Hello World Skill”
            * 6.1.5.2 Click “Continue with template”
        * 6.1.6 On the next page, select "JSON Editor"
            * 6.1.6.1 Drag and drop the mansplaining.json file located in this repository (here: https://github.com/sirimuppala/mansplaining-skill/blob/master/alexa-skill/mansplaining.json)
        * 6.1.7 Navigate to "Code" menu, change invocation name to: "open safe space skill"
        * 6.1.8 Click “Save Model”
        * 6.1.9 Click “Build Model”
    
    * 6.2 Navigate to AWS Console, select Lambda and click on the Lambda function name.
    
    * 6.3 Add trigger (note: You can't create triggers for the $LATEST version, you must create them for a numbered version, as explained here: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/lambda-edge-add-triggers-lam-console.html)
        * 6.3.1 Select a trigger.  Choose AlexaSkill
        * 6.3.2 Enter the Alexa Skill ID collected from the Alexa Developer Console.

7. Set up the proper resources in the mansplaining S3 bucket.

    * 7.1 If not already created, create a folder "meeting-recordings" in the bucket.
    
    * 7.2 Verify that four sub-folders exist: "chime-recordings", "diversity-meetings", "political-discussions", and "technical-meetings". 
    

8. Deploy the Chime meeting recording application
    * Note: The steps outlined below follow the blog post (https://aws.amazon.com/blogs/business-productivity/how-to-enable-client-side-recording-using-the-amazon-chime-sdk/), verify the proper execution with the screenshots included in the post.

    * 8.1 Create Cloud9 environment
        * 8.1.1 Navigate to Cloud9 in AWS Console
        * 8.1.2 Select "Create environment"
        * 8.1.3 Name: enter unique environment name, select "Next step"
        * 8.1.4 Environment settings: 
            * 8.1.4.1 Environment type : Default option ("Create a new EC2 instance for environment (direct access)")
            * 8.1.4.2 Instance type : Select Other instance type and select t3.medium from the dropdown
            * 8.1.4.3 Platform : Amazon Linux
            * 8.1.4.4 Select "Next step"
        * 8.1.5 Review Environment name and settings, select "Create environment". Your Cloud9 environment is now being created, which may take a few minutes.
   
   * 8.2 Create ECR repository, build and push Docker image
        * 8.2.1 Enter the bash shell of the Cloud9 instance, run the following command to create a repository in ECR: 
            * ```aws ecr create-repository --repository-name repository-name```
            * This will return a JSON response containing the repositoryArn value and other details of the newly-created repository.
        * 8.2.2 Execute the following two commands to clone the recording demo in the Cloud9 instance (repository link: https://github.com/aws-samples/amazon-chime-sdk-recording-demo)
            * ```git clone https://github.com/aws-samples/amazon-chime-sdk-recording-demo.git```
            * ```cd amazon-chime-sdk-recording-demo```
        * 8.2.3 Execute the following command, with the value of the repositoryUri generated from 7.2.1, to build and upload the Docker image into ECR.
            * ```make ECR_REPO_URI=<repositoryUri>```
            * This command may take a few minutes to complete running. The output should contain
        * 8.2.4 Navigate to ECR in the AWS Console and verify the image exists
            * 8.2.4.1 Select the ECR repository that has been created, and verify the ImageURI for this repository. 
    
    * 8.3 Set up the recording service
        * 8.3.1 Execute the following command to deploy the CloudFormation stack shipped with the demo, in order to set up the recording service and the other necessary resources. 
            * ```node ./deploy.js -b <my-bucket> -s <my-stack> -i <my-docker-image> -r <region>```
            * Note: The bucket name must follow the S3 bucket naming conventions. 
            * Expect this step to take several minutes to complete. The output will contain the Recording Service URL (save for later).
    
    * 8.4 Configure CopyRecordingLambda trigger through console (Note: this portion can also be automated based on instructions at https://aws.amazon.com/premiumsupport/knowledge-center/cloudformation-s3-notification-lambda/)
            * 8.4.1 Navigate to the AWS Console, select Lambda, and click on the Lambda function name
            * 8.4.2 Add trigger (note: You can't create triggers for the $LATEST version, you must create them for a numbered version, as explained here: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/lambda-edge-add-triggers-lam-console.html)
            * 8.4.3 Select a trigger:
                * 8.4.3.1 Choose S3
                * 8.4.3.2 Bucket : Select the chime-meeting-sdk-<aws-account-id>-<region>-recording-artifacts bucket
                * 8.4.3.3 Event type : PUT
                * 8.4.3.4 Prefix : 2020/
                * 8.4.3.5 Suffix : Leave empty
                * 8.4.3.5 Click "Add"
    
    * 8.5 Start a Chime SDK meeting, with the Chime SDK meeting demo, and multiple participants can join
        * 8.5.1 Download the Chime SDK Meeting demo (repository link: https://github.com/aws/amazon-chime-sdk-js) by executing the following commands:
            * ```cd ../```
            * ```git clone https://github.com/aws/amazon-chime-sdk-js```
            * ```cd demos```
            * ```cd serverless```
            * ```npm install```
        * 8.5.2 Deploy this demo by executing the following command: creates CloudFormation stack, Lambda, and API Gateway resources
            * ```node ./deploy.js -r us-east-1 -b <my-bucket> -s <my-stack-name> -a meeting```
            * Note: The bucket name must follow the S3 bucket naming conventions. 
            * The output will contain the meeting URL, and will look similar to: https://abcdefghij.execute-api.us-east-1.amazonaws.com/Prod/v2
            * Make sure to use the URL ending in "/v2" when joining the meeting in the browser. 
    
    * 8.6 Open the demo meeting using the meeting URL (from step 8.5.2), in your browser.
        * 8.6.1 Specify the meeting name as a unique name you would like.
        * 8.6.2 Specify the user name as a unique name you would like.
        * 8.6.3 Specify the region as the same region you have been creating and deploying all of the previous project resources. 
        * 8.6.4 No need to specify any of the optional settings, and click “Continue”.
        * 8.6.5 Select the appropriate audio and input devices, which you will need to first allow access to, and then click "Join".
        * 8.6.6 You will now be in the meeting. The audio/video controls and screen-share settings are at the top in the middle of the window. Scroll to the bottom, where you will see the list of participants (who is muted/speaking), along with the live video feed for anyone meeting participant who has turned this on. 
        * 8.6.7 You can mimic multiple participants for the single meeting by opening the same meeting URL in multiple tabs in your browser, and make sure to select the same meeting name and region, but a different user name. 

9. Start and stop the meeting recording, by invoking a REST API in API Gateway, using the Postman application.

    * 9.1 Follow the steps highlighted in Postman's developer guide (https://docs.aws.amazon.com/apigateway/latest/developerguide/how-to-use-postman-to-call-api.html) to install and properly set up Postman. 
    
    * 9.2 In Postman, select “AWS Signature" add your AccessKey, SecretKey & AWS Region in the Authorization tab (obtained from IAM in AWS Console).
    
    * 9.3 Start recording:
        * 9.3.1 Name the request, select "POST" for the new request.
        * 9.3.2 Pass the recordingAction as “start” as the first query parameter
        * 9.3.3 Pass the meetingURL (from step 8.5.2) to the recording service as the second query parameter
            * 9.3.3.1 Note: the URL must be URL encoded and must be the same URL (joined from the browser) that ends in "/v2". 
        * 9.3.4 In the "POST" request, you should now "recording?recordingAction=start&meetingURL=...". Prepend the request with the recording service URL from step 8.3.1. 
        * 9.3.5 Start the meeting recording by pressing "SEND". The output should be an arn:aws:ecs:... value.
        * 9.4.6 A new participant should join the meeting (<MeetingRecorder>) -- this is a recording bot that has joined the meeting and will capture the entire web page, both video and audio. 
            * 9.4.6.1 Note: It can take upto 30 seconds for the meeting bot to join the meeting for the first time, and will take under 5 seconds to join after every subsequent recording.
        
    * 9.4 Stop recording:
        * 9.4.1 Pass the ARN that was received in the API response from the previous "POST" request (to start the recording) as "taskId" for the first query parameter
        * 9.5.2 Pass the the recordingAction as “stop” as the second query parameter.
        * 9.5.3 Once the recording stops, the file is uploaded to an S3 bucket.
            * 9.5.3.1 The S3 bucket has the following format: chime-meeting-sdk-<aws-account-id>-<region>-recording-artifacts
            * 9.5.3.2 The recording is saved with the following format: YYYY/MM/DD/HH/<ISO8601 time when meeting started>.mp4
        * 9.5.4 This recording can now be played or edited, as is necessary.

10. Final steps
    
    * 10.1 This will automatically trigger "CopyRecording", which copies the recording to the appropriate mansplaining S3 bucket.
    
    * 10.2 This then triggers "TranscribeLambda" which transcribes the recording and stores in the folder "meeting-transcriptions". 
    
    * 10.3 Once the meeting transcription is created, "AnalyzeMeetingLambda" is triggered, which transcoder the file and the marketplace ML model is run. 
    
    * 10.4 Once analysis is complete, SNS is triggered, at which point the user receives an email, confirming the analysis is complete and with the latest meeting analysis included as well. 
    
    * 10.5 The user can now re-enter the Alexa Developer Console and invoke the skill and retrieve the latest meeting analysis.
        * 10.5.1 Navigate to the "Test" pane on the menu bar. 
        * 10.5.2 Invoke the skill by saying or typing: "open SafeSpace skill"
        * 10.5.3 Retrieve the meeting analysis by saying or typing: "analyze my meeting"
        * 10.5.4 The above command will output the number of meetings already analyzed, along with the same analysis item in the email sent from SNS.

## Troubleshooting Tips:
   * Lambda: 
        * Any code changes can only be made in the $LATEST version. 
        * To properly add triggers, a new version must be published (triggers can only be configured for numbered versions).
   * S3:
        * The file structure of the chime-meeting-sdk-<aws-account-id>-<region>-recording-artifacts bucket is organized by year, month, then day. 
        * After 5:00pm PDT, any new recordings are added to the sub-directory for the next day. 
   * Cloud9:
        * The EBS volume the EC2 instance is running on may run out of disk space at times. In order to resolve this, we can add more space to the volume. Follow the steps outlined here: https://docs.aws.amazon.com/cloud9/latest/user-guide/move-environment.html
        * The two S3 buckets and two CloudFormation stacks created, created through running the two separate deploy.js scripts, must following naming conventions. If a stack or bucket already exists with a name, another one with the same name cannot be created. 
        * Make sure ```npm install``` is run prior to running the second deploy.js script. 
   * Postman:
        * Make sure to use the meeting URL ending in "/v2".
        * The meetingURL value must be the encoded version of the meeting URL.
   * Alexa Developer Console:
        * If any changes are made, in the JSON editor, invocations, etc., the model must be saved and built before the changes can actually take place.
        * In the endpoint menu, for the endpoint service type, under AWS Lambda ARN: verify the default regions (and the other three regions) all match the ARN value of the AlexaSkillLambda function. 
   

## Important References & Resources:
   * [Marketplace ML Model (Audio Gender Classifier)](https://aws.amazon.com/marketplace/pp/prodview-pifmybvuy2cae?qid=1598821336576&sr=0-1&ref_=srh_res_product_title)
   * Chime SDK Integration
        * [Blog Post](https://aws.amazon.com/blogs/business-productivity/how-to-enable-client-side-recording-using-the-amazon-chime-sdk/)
        * GitHub Repositories:
            * [recording-demo](https://github.com/aws-samples/amazon-chime-sdk-recording-demo)
            * [meeting-demo](https://github.com/aws/amazon-chime-sdk-js/tree/master/demos/serverless)
        * [GitHub Reported Issues](https://github.com/aws-samples/amazon-chime-sdk-recording-demo/issues?q=is%3Aissue)
        * [Postman Developer Guide](https://docs.aws.amazon.com/apigateway/latest/developerguide/how-to-use-postman-to-call-api.html)
   * Configuring triggers in Lambda:
        * [Trigger cannot be configured on $LATEST version](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/lambda-edge-add-triggers-lam-console.html)
        * [Automate adding triggers](https://aws.amazon.com/premiumsupport/knowledge-center/cloudformation-s3-notification-lambda/)
