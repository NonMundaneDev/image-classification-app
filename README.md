# Image Classication Application on Serverless
A demo application for a technical guide showing how to deploy image classification applications on serverless environments following best practices using serverless computing.

## Architectural Pattern

### Continuous Integration/Continuous Delivery Workflow
Here’s what the CI/CD architecture looks like:

![Continuous Integration/Delivery workflow](ci_cd_workflow_neptuneai_article.png?raw=true "Title")


Here, an [IAM](https://aws.amazon.com/iam/) user will use [AWS CLI](https://aws.amazon.com/cli/) and git client to push our application code and some configuration files to a private [CodeCommit](https://aws.amazon.com/codecommit/) repository. This new commit will trigger [CodePipeline](https://aws.amazon.com/codepipeline/) to create a new build for the [Docker](https://www.docker.com/) image from our [Dockerfile](https://docs.docker.com/engine/reference/builder/) and a specified build configuration using [CodeBuild](https://aws.amazon.com/codebuild/). Once the build is done and has succeeded, the Docker image will be pushed to a private registry in [AWS ECR](https://aws.amazon.com/ecr/). You can now use the Docker image to create the [Lambda function](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html) that’ll serve as the inference endpoint in production.


---
### Deployment workflow
Here’s what the deployment architecture looks like:

![Serverless backend deployment workflow](deployment_workflow_neptuneai_article.png?raw=true "Title")

The flow is stated on the image. You create a Lambda function inference endpoint with the Docker image you built from your ECR repository. At this point, you will test the function before deploying it. Once it’s deployed, you can now perform an end-to-end test by uploading a new image to the S3 bucket you created, this triggers the Lambda function that spins up your containerized application, runs a prediction, and returns the results to the DynamoDB table.

---

### Note

You can customize the code files to your needs. Ensure you replace the necessary tags and understand the structure of the functions. You can also instruct the [`Dockerfile`](Dockerfile) to download your own model instead.

---

### Pre-requisites to implement this architecture

To successfully along with this guide, here are some things you should know and have:
* A [free tier AWS account](https://aws.amazon.com/free/) or an active account with up to $3 in it. Following along with this guide should cost less than $3 as of the time of publication.
* Basic experience using AWS cloud and the [command-line interface tool](https://aws.amazon.com/cli/) is [set up](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) and configured to work with your IDE. You can install the full AWS toolkit for VSCode [here](https://aws.amazon.com/visualstudiocode/).
* Basic interaction with [Docker](https://docs.docker.com/get-docker/) CLI.
* An active [IAM user](https://docs.aws.amazon.com/IAM/latest/UserGuide/id.html) is defined preferably (for security best practices). I’d advise you not to use the root user for this technical guide. You can provide access to the services listed below for the user:
    * [AWS Lambda](https://aws.amazon.com/lambda/).
    * AWS [CodeBuild](https://aws.amazon.com/codebuild/), [CodeCommit](https://aws.amazon.com/codecommit/), and [CodePipeline](https://aws.amazon.com/codepipeline/).
    * [AWS Elastic Container Registry (ECR)](https://aws.amazon.com/ecr/).
    * [Amazon S3](https://aws.amazon.com/s3/).
    * [Amazon API Gateway](https://aws.amazon.com/api-gateway/).
    * [Amazon DynamoDB](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Introduction.html).
    * [Amazon Cloudwatch](https://aws.amazon.com/cloudwatch/) and [Cloudwatch Logs](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/WhatIsCloudWatchLogs.html).

---
* [`iam_policy`](iam_policy) contains the policy for the IAM user I created for this guide. Modify with your own `account ID`.

* [`s3_bucket`](s3_bucket) contains the sample public read policy for the bucket that will hold the inference images.

* [`test_images`](test_images) contains images for testing the application once it is live.