# -*- coding: utf-8 -*-
"""
Created on Fri Apr  2 14:21:23 2021

@author: sconcannon
"""

import xml.etree.ElementTree as ET
from datetime import datetime
import requests
import dateutil.parser
import os
import shutil
from string import Template
import urllib.request
import zipfile
from imageDl import imgDl
from makeManifest import makeManifest


# settings
doi_suffix_prepend = 'pc'
doi_prefix = '10.1073'
input_file = 'data/211023_libsyn_rss.xml'
do_type = 'podcast'
group_doi = '10.1073/podcast-do-group'
clientSiteBaseUrl = 'http://pnas.org'
doBaseUri = doi_prefix + "/" + do_type
player_markup_temp = Template('<atpn:libsynPlayer><![CDATA[<iframe style="border: none" src="//html5-player.libsyn.com/embed/episode/id/$PLAYERID/height/90/theme/custom/thumbnail/yes/direction/backward/render-playlist/no/custom-color/ec1e1e/" height="90" width="100%" scrolling="no" allowfullscreen="true" webkitallowfullscreen="true" mozallowfullscreen="true" oallowfullscreen="true" msallowfullscreen="true"></iframe>]]></atpn:libsynPlayer>')
errorfile = r"C:\Users\sconcannon\libsyn_to_DO\output\errors.txt"

ns = {"atom":"http://www.w3.org/2005/Atom",
      "cc":"http://web.resource.org/cc/",
      "itunes":"http://www.itunes.com/dtds/podcast-1.0.dtd",
      "media":"http://search.yahoo.com/mrss/",
      "content":"http://purl.org/rss/1.0/modules/content/",
      "podcast":"https://podcastindex.org/namespace/1.0",
      "googleplay":"http://www.google.com/schemas/play-podcasts/1.0",
      "rdf":"http://www.w3.org/1999/02/22-rdf-syntax-ns#",
      "libsyn":"http://libsyn.com/libsyn-rss-spec"}

# build datetime suffix for submission package YYYYMMDDHHMM
date = datetime.today()
timestamp = str(date.strftime("%Y%m%d%H%M"))

count = 0

tree = ET.parse(input_file) 
root = tree.getroot()
items = root.findall("./channel/item") # list of posts

def log_error(error, errorfile):
    error_message = timestamp + ": " + error + "\n"
    with open(errorfile,'a') as ef:
        ef.write(error_message)
        
def zipfolder(foldername, target_dir):
    zipobj = zipfile.ZipFile(foldername + '.zip', 'w', zipfile.ZIP_DEFLATED)
    rootlen = len(target_dir) + 1
    for base, dirs, files in os.walk(target_dir):
        for file in files:
            fn = os.path.join(base, file)
            zipobj.write(fn, fn[rootlen:])
    zipobj.close()
    
def getPlayerMarkup(player_id):
    markup = player_markup_temp.substitute(PLAYERID = player_id)
    return markup

for post in items:
    relation = ""
    transcript = ""
    fileXml = ""
    transcriptField=""
    post_title = post.find('title').text
    unformattedDate = post.find('pubDate').text
    pubDate = str(dateutil.parser.parse(unformattedDate).isoformat())
    download_link = post.find('link').text
    description = post.find('description').text
    player_id = post.find("libsyn:itemId", ns).text
    # player_markup = getPlayerMarkup(player_id)
    duration = post.find('itunes:duration', ns).text
    duration_markup = '<atpn:duration>' + duration + '</atpn:duration>'
    cats = post.findall('category')
    for cat in cats:
        if cat.text[:7] == "10.1073":
            reldoi = cat.text
            relation = "<mods:relatedItem xmlns:mods=\"http://www.loc.gov/mods/v3\" xlink:href=\"" + cat.text + "\" ID=\"associatedArticle\"></mods:relatedItem>"
        if cat.text[:4] == "http":
            transcript = cat.text
            transcriptfn = transcript.split("/")[-1]
            transcriptfn = transcriptfn.replace("\n","")
            transcriptfnSafe = transcriptfn.lower()
            transcriptXml = \
                    "    <mets:fileGrp ID=\"transcript-group\">\n" + \
                    "        <mets:file ID=\"transcriptPDF\">\n" + \
                    "            <mets:FLocat LOCTYPE=\"URL\" xlink:href=\"file://" + transcriptfnSafe + "\"></mets:FLocat>\n" + \
                    "        </mets:file>\n" + \
                    "    </mets:fileGrp>\n"
            fileXml = fileXml + transcriptXml
            transcriptField = "<atpn:transcriptPDF>" + transcriptfnSafe + "</atpn:transcriptPDF>"
    if ( mi := post.find('itunes:image', ns) ) is not None:
        mainImageUrl = mi.attrib['href']
        mainImageFilename = mainImageUrl.split("/")[-1]
        mainImageFilename = mainImageFilename.replace("\n","")
        mainImagefnSafe = mainImageFilename.lower()
        if mainImageFilename != "PNAS_podcast_1400x1400.jpg":
            imageXml = \
                    "    <mets:fileGrp ID=\"mainimage-group\">\n" + \
                    "        <mets:file ID=\"mainimage344138528\">\n" + \
                    "            <mets:FLocat LOCTYPE=\"URL\" xlink:href=\"file://" + mainImagefnSafe + "\"></mets:FLocat>\n" + \
                    "        </mets:file>\n" + \
                    "    </mets:fileGrp>\n"
            fileXml = fileXml + imageXml
            mainImageField = "<atpn:mainimage>" + mainImagefnSafe + "</atpn:mainimage>"
        else:
            mainImageUrl = ""
            mainImageFileName = ""
            mainImagefnSafe = ""
            mainImageField = ""
        
    if fileXml != "":
        fileXml = "<mets:fileSec xmlns:mets=\"http://www.loc.gov/METS/\">\n" + fileXml +  "</mets:fileSec>\n"
    doi_suffix = doi_suffix_prepend + '.' + player_id
    outputdoi = doi_prefix + '/' + doi_suffix
    doFolder = do_type + "_" + doi_suffix + "_" + timestamp + "/" + doi_suffix
    meta = "meta"
    output = "output"
    doFolderPath = os.path.join(output,timestamp,doFolder,meta)
    attachmentsPath = os.path.join(output, timestamp, doFolder)
    os.makedirs(doFolderPath)
    filename = "output/" + timestamp + "/" + doFolder + "/meta/" +doi_suffix+ ".xml"
    safeTranscriptPath = "output/" + timestamp + "/" + "podcast_" + doi_suffix + "_" + timestamp + "/" + doi_suffix + "/" + transcriptfnSafe
    transcriptPath = "output/" + timestamp + "/" + "podcast_" + doi_suffix + "_" + timestamp + "/" + doi_suffix + "/" + transcriptfn
    mainImagePath = "output/" + timestamp + "/" + "podcast_" + doi_suffix + "_" + timestamp + "/" + doi_suffix + "/" + mainImageFilename
    safeMainImagePath = "output/" + timestamp + "/" + "podcast_" + doi_suffix + "_" + timestamp + "/" + doi_suffix + "/" + mainImagefnSafe
    manifestFile = "output/"+ timestamp + "/" + do_type + "_"+doi_suffix+ "_" + timestamp + "/manifest.xml"
    with open(manifestFile, 'w') as outfile:
        manifestXml = makeManifest(group_doi)
        outfile.write(manifestXml)
    with open('input/sample.txt') as infile, open(filename, 'w', 1, 'utf-8') as outfile:
        for line in infile:
            line = line.replace("DO_TYPE_REPLACE", do_type)
            line = line.replace("DO_DOI_REPLACE", outputdoi)
            line = line.replace("DO_TITLE_REPLACE", post_title)
            line = line.replace("DO_BASE_DOI_REPLACE", doBaseUri)
            line = line.replace("DO_DATE_REPLACE", pubDate)
            line = line.replace("DO_LIBSYN_PLAYER_REPLACE", player_id)
            line = line.replace("DO_DURATION_REPLACE", duration_markup)
            # replacer for relation
            line = line.replace("DO_RELATION_REPLACE", relation)
            # replacer for filesec
            line = line.replace("DO_FILESEC_REPLACE", fileXml)
            line = line.replace("DO_MAININAGE_REPLACE", mainImageField)
            line = line.replace("DO_TRANSCRIPT_REPLACE", transcriptField)
            
            outfile.write(line)
    
    if mainImageUrl != "":
        try:
            imgDl(mainImageUrl, attachmentsPath)
            os.rename(mainImagePath, safeMainImagePath)
        except Exception as e:
            this_error = str(e) + " - could not download main image"
            log_error(this_error, errorfile)
            print(this_error)
            
    if transcript != "":
        try:
            imgDl(transcript, attachmentsPath)
            os.rename(transcriptPath, safeTranscriptPath)
        except Exception as e:
            this_error = str(e) + " - could not download transcript"
            log_error(this_error, errorfile)
            print(this_error)    
        
    zipfolder("output/" + timestamp + "/" + do_type + "_" + doi_suffix + "_" + timestamp, 
                  "output/" + timestamp +"/" + do_type + "_" +doi_suffix + "_" + timestamp)
       
    shutil.rmtree("output/" + timestamp + "/" + do_type + "_" +doi_suffix + "_" + timestamp)
    count+=1
    print(str(count) + '-' + str(player_id))
    
    
    
        
    