# mansplaining-skill


#Instructions

1. Launch the prep cloudformation stack
2. Verify the resources
3. Configure Lambda trigger through console (Note : this portiona can also be automated based on instructions at https://aws.amazon.com/premiumsupport/knowledge-center/cloudformation-s3-notification-lambda/ )
3.1 Click on the lambda function name
3.2 Add trigger
3.3 Select a trigger.  Choose S3
3.4 Bucket : Select the mansplaining bucket.
3.5 Event type : PUT
3.6 Prefix : meeting-recordings/
3.7 Suffix : Leave empty
3.8 Click Add