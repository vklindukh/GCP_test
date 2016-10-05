Test App Engine application
- get file from POST
- update Datastore
- upload file to Google Storage
- generate signed URL
- send email to customer with generated URL

Deploy:

gcloud app deploy app.yaml 

Usage:

curl -F "token=<TOKEN>" -F "email=<RECiPIENT EMAIL>" -F "filename=<FILENAME>" -F "content=@<FILEPATH>" https://<APPENGINE-INSTANCE>.appspot.com/upload
