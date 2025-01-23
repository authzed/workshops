## Setup and Prerequisites

Lets start with the setup for this workshop.

- Access to a SpiceDB instance running on [AuthZed Serverless](https://authzed.com/products/authzed-serverless) instance. Sign up for free [here](http://app.authzed.com)
- A [Pinecone account](https://www.pinecone.io/) and API key
- An [OpenAI Platform account](https://platform.openai.com/docs/overview) and API key
- A Google Colab notebook that is shared in the next step. 

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

### Troubleshooting


