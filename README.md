# SmartGoogleDrive
This program allows users to Query documents and folders from their google drive by describing them with their voice or through text without needing to know the exact name of the file or folder.

It uses vector embeddings of the summaries made by an LLM of each item in your drive and the folders containing those files. When you want to query a document it does a similarity search between your query vector embedding and the vector embedding database for your drive.

As a result you find documents or folders according to a description of them or what you are looking for. This is a short demo video: https://youtu.be/0Vr6zo-AGws 
![](https://github.com/MrJellyBean3/SmartGoogleDrive/blob/main/SmartDriveDemo.gif)
