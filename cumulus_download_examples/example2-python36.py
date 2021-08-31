'''
This is an example Cumulus download script 
using Python3 and requests module/library.
'''
import os, json, time, requests

def get_download_status(url):
    response = requests.get(url)
    return response.json()


# Should probably store these as env variables or at the very least
# set script permissions so that only owner can read it.
# Use the web ui to acquire (user profile screen)
token_id = 'ADD-YOUR-TOKEN-ID-HERE'
secret_token = 'ADD-YOUR-SECRET-KEY-HERE'

payload = {}
payload["datetime_start"] = "2021-08-27T10:00:00Z"
payload["datetime_end"] = "2021-08-31T23:59:59Z"

# LRH Big Sandy
# Reference: https://cumulus-api.rsgis.dev/watersheds
payload["watershed_id"] = "3e322a11-b76b-4710-8f9a-b7884cd8ae77"  

# MRMS V12 Pass2
# Reference: https://cumulus-api.rsgis.dev/products
payload["product_id"] = ["7c7ba37a-efad-499e-9c3a-5354370b8e9e"]

# Define the API Endpoint with proper key auth
url = 'https://cumulus-api.rsgis.dev'
post_url = url+'/my_downloads?key_id='+token_id+'&key='+secret_token
get_url = url+'/downloads'

# Send the request with payload
print('\nSending payload\n'+json.dumps(payload)+'\n')
try:
    req = requests.post(post_url, json=payload)

    # Read the Response
    download_id = req.json()['id']   

    # Try for 300 seconds (5 mins) before timing out
    MAX_TRIES = 30
    WAIT_TIME = 10 #seconds
    counter = 1

    # Initial download status check to start while loop
    ds = get_download_status(get_url+'/'+download_id)

    while int(ds['progress']) != 100 and counter < MAX_TRIES:
        print('Progress: {}% | Status Check: #{}'.format(str(ds['progress']).zfill(2), counter))
        counter = counter+1
        time.sleep(WAIT_TIME)
        ds = get_download_status(get_url+'/'+download_id)

    if ds['file'] is not None:
        print('Downloading file: '+ds['file'])
        with open('/Users/dev/Desktop/'+os.path.basename(ds['file']), "wb") as of:
            # get request
            r = requests.get(ds['file'])
            # write to file
            of.write(r.content)

except Exception as e: 
    print(e)