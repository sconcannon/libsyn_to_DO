# -*- coding: utf-8 -*-
"""
Created on Sun May  9 05:28:37 2021

@author: sconcannon
"""

def makeManifest (groupDoi):
    manifestXml = \
        "<!DOCTYPE submission PUBLIC \"-//Atypon//DTD Literatum Content Submission Manifest DTD v4.2 20140519//EN\" \"manifest.4.2.dtd\">\n" +\
        "<submission dtd-version=\"4.2\" group-doi=\"" + groupDoi + "\" submission-type=\"full\">\n" + \
        "   <processing-instructions>\n" + \
        "      <make-live on-condition=\"no-fatals\"/>\n" + \
        "   </processing-instructions>\n" + \
        "</submission>"
    return manifestXml
    
    