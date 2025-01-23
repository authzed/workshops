## Setup and Prerequisites

Lets start with the setup for this workshop.

- Access to a SpiceDB instance running on [AuthZed Serverless](https://authzed.com/products/authzed-serverless) instance. Sign up for free [here](http://app.authzed.com)
- A [Pinecone account](https://www.pinecone.io/) and API key
- An [OpenAI Platform account](https://platform.openai.com/docs/overview) and API key
- A Google Colab notebook that is shared in the next step (requires a Google Account)

#### Running SpiceDB

Once you've signed into AuthZed Serverless, click on the **Create Permissions System** button. 
Add the following details;

- System Kind: Development
- Object Prefix: This is a globally unique ID that is used to identify all the objects in your Permissions System. Choose an alphanumeric value and note it down for future use.
- Name: rag-permissions 
- Description: Secure your RAG pipeline with fine-grained authorization

![create new](https://github.com/authzed/workshops/blob/google-colab/secure-rag-pipelines/assets/create-new.png)

Once the Permissions System is created, click on it and navigate to the "API Access Permissions" tab. 

![API Access Permissions](https://github.com/authzed/workshops/blob/google-colab/secure-rag-pipelines/assets/dashboard.png)

Click on the default client that has already been created for you and then the Create Token button. Add the following details:

- Token Title: workshop
- Token Note: A token granting access to the cloud notebook

![create new token](https://github.com/authzed/workshops/blob/google-colab/secure-rag-pipelines/assets/create-token.png)

Copy the token that is generated as it will not be displayed again. 


## Navigation

Proceed to [this Google Colab notebook](https://colab.research.google.com/drive/1933-bS7TqEVSOFVg-BHSC1lGuHO3IOy5?usp=sharing) to start the workshop.  

---

#### Troubleshooting

**1. OpenAI API rate limit error**

`RateLimitError: Error code: 429 - {'error': {'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, read the docs: https://platform.openai.com/docs/guides/error-codes/api-errors.', 'type': 'insufficient_quota', 'param': None, 'code': 'insufficient_quota'}}`

This means you are out of free OpenAI API credits, or your free tokens have expired. You need to upgrade to a Paid tier. More details can be found in [this StackOverflow page](https://stackoverflow.com/questions/75898276/openai-api-error-429-you-exceeded-your-current-quota-please-check-your-plan-a)


**2. The Google Colab notebook does not connect to the Google Compute Engine**

Sometimes the cloud notebook is stuck while connecting to Google Compute Engine. Follow these steps for your notebook get connected:

- Delete cookies
- Turn off browser extensions (such as AdBlock) that might interfere with the cloud notebook
- Restart connection to the notebook

**3. I don't have a Google Account / AuthZed Serverless Account**

You can run this using Jupyter notebook and SpiceDB installed locally. [Here're the step-by-step](https://github.com/authzed/workshops/tree/jupyter) instructions on how to do so.