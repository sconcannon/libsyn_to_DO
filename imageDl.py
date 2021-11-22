# -*- coding: utf-8 -*-
"""
Created on Sun Apr 25 10:07:28 2021

@author: sconcannon
"""
import requests
import shutil

def imgDl(image_url, image_folder):
    '''download a file from a url - returns the filename and request status'''
    filename = image_url.split("/")[-1]
    filepath = image_folder + "/" + filename
    headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36', 
               'Referrer': 'https://pnas-science-sessions-podcast.libsyn.com/website'}
    
    # open image url & set stream to true to prevent interruptions
    r = requests.get(image_url, headers=headers, stream = True)
    status = r.status_code
    # check is the image was retrieved correctly
    if status == 200:
        # Set decode_content value to True, otherwise the download image 
        # filesize will be zero
        r.raw.decode_content = True
      
        # Open a local file with wb (write binary) permission.
        with open(filepath, 'wb') as f:
            shutil.copyfileobj(r.raw, f)
        print('downloaded ',filename)
    
    return(status, filename)
    