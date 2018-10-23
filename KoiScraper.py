# -*- coding: utf-8 -*-
"""
Import koi pictures and data from web sites

Functions assume current working directory is 
c:\\Users\\clorja\\Documents\\Personal\\KoiProject\\WebScraping with:
1. folders for pictures from each website
2. folders for old .csv files from each website

"""

import requests
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import urllib
import time
import os

def scrape_web():
    KodamaImport()
    KloubecImport()
    ChampImport()

def KodamaImport():
    
    #Find previous data file
    previous_data_file=('')
    for file in os.listdir(os.getcwd()):
        if file.startswith('Kodama') & file.endswith('.csv'):
            previous_data_file=file
            prev_data=pd.read_csv(previous_data_file)
            break          

    ID = []
    Type = []
    PicFile = []
    BuyItNow = []
    FinalBid = []
    Size = []
    Sex = []
    Breeder = []
    DateAdded = []
    
    #Check that length of previous data file is the same as the number of pictures:
    num_pictures=len(os.listdir('KodamaPics'))        
    if previous_data_file !=  '':
        assert prev_data.shape[0] == num_pictures, \
        'Number of rows in existing data file not equal to number of pictures'
        
    Last_Page_IDs = []
    for i in range(1, 50):
        page=i
        url = 'https://www.kodamakoifarm.com/lover/auction.php?page='+str(page)+')'
        print('Working on page %d of Kodama' %page)
    
        r=requests.get(url, timeout=30)
        html_doc=r.text
        soup=BeautifulSoup(html_doc)
        pretty_soup=soup.prettify()
        
        #identify IDs on each page:
        #Assume IDs are listed as ID 12XXXX
        #Assume ID's are separated by abut 3500 characters
        #Typically there will be 12 on each page, except the last page
        LISTING_LENGTH = 3500
        index = 0

        IDsIndex = []
        IDs = []

        while index < len(pretty_soup):
            index = pretty_soup.find('ID 12', index)
            if index == -1:
                break
            IDsIndex.append(index)
            index=index+3
            end_index = index + 9
            this_id = pretty_soup[index:end_index]
            IDs.append(int(this_id))
            index = index + LISTING_LENGTH

        #check to see if this page is the same as the last one. If so,
        #we're done.
        if IDs == Last_Page_IDs or len(IDs) == 0:
            print('The previous page was the last one')
            break
        Last_Page_IDs=list(IDs)
        
        if len(IDs) != 12:
            print('Fewer than 12 IDs on this page:\nOK if this is the last page')  
        
        
        #For each ID, if it's already recorded, just check to see
        #if the final price should be updated
        #Else extract data and add to lists
        
        for idx,index in enumerate(IDsIndex):
            end_of_index = index + LISTING_LENGTH
            
            #If we have existing data, check for this ID
            already_recorded = False
            if 'prev_data' in locals():
                if IDs[idx] in prev_data['ID'].values:
                    already_recorded = True
            
            #If this ID exists, check to see if we already have a final bid
            #this could be "closed" or "Buy it now:sold"
            if already_recorded == True:
                index_in_master = prev_data['ID'][prev_data['ID']==
                                            IDs[idx]].index.tolist()[0]
                if prev_data.loc[index_in_master]['FinalBid']!='[]':
                    print('Skipping ID %d: already completely populated' %IDs[idx])
                else:
                    is_closed = pretty_soup.find('Closed',index, end_of_index)
                    buyitnow_sold = pretty_soup.find('Buy It Now:Sold',index, end_of_index)
                    is_closed = max(is_closed, buyitnow_sold)
                    if is_closed == -1:
                        print('Skipping ID %d: already populated but not closed' %IDs[idx])
                    else:
                        location_start = pretty_soup.find('Current Bid:', index, end_of_index)
                        assert location_start>1
                        location_end = pretty_soup.find('.-',location_start)
                        location_start += 14
                        this_final_bid = pretty_soup[location_start:location_end].strip()
                        #there might be a comma if it's more than $1,000:
                        this_final_bid = this_final_bid.replace(',','')
                        this_final_bid = float(this_final_bid)     
                        prev_data.set_value(index_in_master,'FinalBid',this_final_bid)
                        print('Updated final value of ID %d' %IDs[idx])
                    
            #If this ID doesn't exists, fill it in
            else:
                print('Working on ID %d' %IDs[idx])
                
                #Add ID to list
                ID.append(IDs[idx])
                
                #Get Type as string
                location_start = pretty_soup.find('"auction">', index, end_of_index)
                if location_start == -1:
                    Type.append([])
                else:
                    location_end = pretty_soup.find('</span>',location_start)
                    location_start += 11
                    this_type = pretty_soup[location_start:location_end].strip()
                    Type.append(this_type)
                    
                #Save picture as Kodama[ID]
                this_ID = IDs[idx]
                file_name = 'KodamaPics\Kodama[' + str(this_ID) +'].jpg'
                location_start = pretty_soup.find('<!-- //', index, end_of_index)
                if location_start == -1:
                    print('No picture for')
                else:
                    location_end = pretty_soup.find('-->',location_start)
                    location_start +=7
                    link = pretty_soup[location_start:location_end].strip()
                    link = 'http://' + link 
                    #use the large photo rather than the small one
                    link=link.replace('s/s/','s/')
                    urllib.request.urlretrieve(link, file_name)
                    PicFile.append(file_name)
                
                #Get Buy it Now as float
                location_start = pretty_soup.find('Buy It Now: ', index, end_of_index)
                if location_start == -1:
                    BuyItNow.append([])
                else:
                    location_end = pretty_soup.find('.-',location_start)
                    location_start += 13
                    this_buyitnow = pretty_soup[location_start:location_end].strip()
                    #there might be a comma if it's more than $1,000:
                    this_buyitnow = this_buyitnow.replace(',','')
                    this_buyitnow = float(this_buyitnow)
                    BuyItNow.append(this_buyitnow)
                    
                #If the auction is closed add a final value
                is_closed = pretty_soup.find('Closed',index, end_of_index)
                if is_closed == -1:
                    FinalBid.append([])
                else:
                    location_start = pretty_soup.find('Current Bid:', index, end_of_index)
                    assert location_start>1
                    location_end = pretty_soup.find('.-',location_start)
                    location_start += 14
                    this_final_bid = pretty_soup[location_start:location_end].strip()
                    #there might be a comma if it's more than $1,000:
                    this_final_bid = this_final_bid.replace(',','')
                    this_final_bid = float(this_final_bid)
                    FinalBid.append(this_final_bid)
                    
                #Get Size as float (in cm)
                location_end = pretty_soup.find(' cm ',index, end_of_index)
                if location_end == -1:
                    Size.append([])
                else:            
                    location_start = location_end-6
                    this_size = pretty_soup[location_start:location_end].strip()
                    this_size = float(this_size)
                    Size.append(this_size)
        
                #Get Sex as string
                location_start = pretty_soup.find('Sex: ', index, end_of_index)
                if location_start == -1:
                    Sex.append([])
                else:
                    location_end = pretty_soup.find('<br/>',location_start)
                    location_start += 4
                    this_sex = pretty_soup[location_start:location_end].strip()
                    Sex.append(this_sex)  
                    
                #Get Breeder as string
                location_start = pretty_soup.find('Breeder:', index, end_of_index)
                location_start = pretty_soup.find('700)">', location_start,
                                                  end_of_index)
                if location_start == -1:
                    Breeder.append([])
                else:
                    location_end = pretty_soup.find('</a>',location_start)
                    location_start += 6
                    this_breeder = pretty_soup[location_start:location_end].strip()
                    Breeder.append(this_breeder)  
                    
                #Add todays date
                DateAdded.append(time.strftime('%Y_%m_%d'))
                
    #If this is the first time, create Pandas Dataframe with the information
    #otherwise add it to the existing file
    Kodama = pd.DataFrame({'ID':ID,'Type':Type,
                               'BuyItNow':BuyItNow,'Size':Size,'Breeder':Breeder,
                               'Photo':PicFile, 'DateAdded':DateAdded, 'Sex':Sex,
                               'FinalBid':FinalBid})
    Kodama['Website'] = 'Kodama'
    if previous_data_file ==  '':
        file_name = ('Kodama_' + time.strftime('%Y_%m_%d') + '.csv')
        Kodama.to_csv(file_name, index=False)
    else:
        new_data_file = prev_data.append(Kodama, ignore_index=True)
        file_name = ('Kodama_' + time.strftime('%Y_%m_%d') + '.csv')
        new_data_file.to_csv(file_name, index=False)
        #move old file to archive
        archive_location = 'KodamaOldFiles/' + previous_data_file
        os.rename(previous_data_file, archive_location)
        
        #Check that length of new data file is the same as the number of pictures:
        num_pictures = len(os.listdir('KodamaPics'))        
        assert new_data_file.shape[0] == num_pictures, \
        'Number of rows in new data file not equal to number of pictures'

def KloubecImport():
    
    #Find previous data file
    previous_data_file=('')
    for file in os.listdir(os.getcwd()):
        if file.startswith('Kloubec') & file.endswith('.csv'):
            previous_data_file=file
            prev_data=pd.read_csv(previous_data_file)
            break          

    ID = []
    Type = []
    PicFile = []
    BuyItNow = []
    FinalBid = []
    Size = []
    Sex = []
    Breeder = []
    DateAdded = []
    
    #Check that length of previous data file is the same as the number of pictures:
    num_pictures=len(os.listdir('KloubecPics'))        
    if previous_data_file !=  '':
        assert prev_data.shape[0] == num_pictures, \
        'Number of rows in existing data file not equal to number of pictures'
        
    Last_Page_IDs = []
    for i in range(1, 20):
        page=i
        url = 'https://www.kloubeckoi.com/koi-for-sale/?sort=featured&page='+str(page)
        print('Working on page %d of Kloubec' %page)
    
        r=requests.get(url, timeout=30)
        html_doc=r.text
        soup=BeautifulSoup(html_doc)
        pretty_soup=soup.prettify()
        
        #identify IDs on each page:
        #Assume ID's are separated by abut 3500 characters
        #The number of listings on each page varies
        LISTING_LENGTH = 600
        index = 0

        IDsIndex = []
        IDs = []

        while index < len(pretty_soup):
            index = pretty_soup.find('ProductImage QuickView" data-product=', index)
            if index == -1:
                break
            index=pretty_soup.find('#', index)
            index = index + 1
            IDsIndex.append(index)
            
            end_index = pretty_soup.find(")'", index)
            this_id = pretty_soup[index:end_index]
            IDs.append(this_id)
            index = index + LISTING_LENGTH

        #check to see if this page is the same as the last one. If so,
        #we're done.
        if IDs == Last_Page_IDs:
            print('The previous page was the last one')
            break
        Last_Page_IDs=list(IDs)
        
        for idx,index in enumerate(IDsIndex):
            end_of_index = index + LISTING_LENGTH
            
            #If we have existing data, check for this ID
            already_recorded = False
            if 'prev_data' in locals():
                if IDs[idx] in prev_data['ID'].values:
                    already_recorded = True
            
            #If this ID exists, skip it
            if already_recorded == True:
                print('Skipping ID %s: already recorded' %IDs[idx])
                    
            #If this ID doesn't exists, fill it in
            else:
                print('Working on ID %s' %IDs[idx])
                
                #Add ID to list
                ID.append(IDs[idx])
                
                #Get Size as float (convert to cm)
                start = index - 50
                location_start = pretty_soup.find("img alt='",start, end_of_index)
                if location_start == -1:
                    Size.append([])
                else:            
                    location_start = location_start+9
                    location_end = pretty_soup.find('"',location_start, end_of_index)
                    this_size = pretty_soup[location_start:location_end]
                    #Check to see if this is a number
                    try:
                        this_size = float(this_size)
                        this_size = this_size * 2.54
                    except ValueError:
                        this_size = []
                    Size.append(this_size)
                
                #Get Type as string
                location_start = location_end+2
                if location_start == -1:
                    Type.append([])
                else:
                    location_end = pretty_soup.find(' (#',location_start)
                    this_type = pretty_soup[location_start:location_end]
                    Type.append(this_type)
                    
                #Save picture as Kloubec[ID]
                this_ID = IDs[idx]
                file_name = 'KloubecPics\Kloubec[' + this_ID +'].jpg'
                location_start = pretty_soup.find('src="', index, end_of_index)
                if location_start == -1:
                    print('No picture for')
                else:
                    location_end = pretty_soup.find('"/>',location_start)
                    location_start += 5
                    link = pretty_soup[location_start:location_end].strip()
                    urllib.request.urlretrieve(link, file_name)
                    PicFile.append(file_name)
                
                #BuyItNow is NA
                    BuyItNow.append([])

                #Add price
                location_start = pretty_soup.find('="p-price">', index, end_of_index)
                #Check for a sale
                alt_start = pretty_soup.find('alePrice">', index, end_of_index)
                location_start = max([location_start, alt_start])
                assert location_start>1
                
                location_end = pretty_soup.find('</em>',location_start)
                alt_end = pretty_soup.find('</span>',location_start)
                location_end = min ([location_end, alt_end])
                
                location_start += 11
                this_final_bid = pretty_soup[location_start:location_end].strip()
                #Remove dollar signs and commas, if they exist
                this_final_bid = this_final_bid.replace('$','')
                this_final_bid = this_final_bid.replace(',','')
                this_final_bid = float(this_final_bid)
                FinalBid.append(this_final_bid)
        
                #Sex is NA
                Sex.append([])
                    
                #Breeder is NA
                Breeder.append([])
                    
                #Add todays date
                DateAdded.append(time.strftime('%Y_%m_%d'))
                
    #If this is the first time, create Pandas Dataframe with the information
    #otherwise add it to the existing file
    Kloubec = pd.DataFrame({'ID':ID,'Type':Type,
                               'BuyItNow':BuyItNow,'Size':Size,'Breeder':Breeder,
                               'Photo':PicFile, 'DateAdded':DateAdded, 'Sex':Sex,
                               'FinalBid':FinalBid})
    Kloubec['Website'] = 'Kloubec'
    if previous_data_file ==  '':
        file_name = ('Kloubec_' + time.strftime('%Y_%m_%d') + '.csv')
        Kloubec.to_csv(file_name, index=False)
    else:
        new_data_file = prev_data.append(Kloubec, ignore_index=True)
        file_name = ('Kloubec_' + time.strftime('%Y_%m_%d') + '.csv')
        new_data_file.to_csv(file_name, index=False)
        #move old file to archive
        archive_location = 'KloubecOldFiles/' + previous_data_file
        os.rename(previous_data_file, archive_location)
        
        #Check that length of new data file is the same as the number of pictures:
        num_pictures = len(os.listdir('KloubecPics'))        
        assert new_data_file.shape[0] == num_pictures, \
        'Number of rows in new data file not equal to number of pictures'

def ChampImport():
    
    #Find previous data file
    previous_data_file=('')
    for file in os.listdir(os.getcwd()):
        if file.startswith('Champ') & file.endswith('.csv'):
            previous_data_file=file
            prev_data=pd.read_csv(previous_data_file)
            break          

    ID = []
    Type = []
    PicFile = []
    BuyItNow = []
    FinalBid = []
    Size = []
    Sex = []
    Breeder = []
    DateAdded = []
    
    #Check that length of previous data file is the same as the number of pictures:
    num_pictures=len(os.listdir('ChampPics'))        
    if previous_data_file !=  '':
        assert prev_data.shape[0] == num_pictures, \
        'Number of rows in existing data file not equal to number of pictures'
        
    Last_Page_IDs = []
    for i in range(1, 50):
        page=i
        url = 'http://www.champkoi.com/koi/?page='+str(page)
        print('Working on page %d of Champion' %page)
    
        r=requests.get(url, timeout=30)
        html_doc=r.text
        soup=BeautifulSoup(html_doc)
        pretty_soup=soup.prettify()
        
        #identify IDs on each page:
        #Assume IDs are listed as ID 12XXXX
        #Assume ID's are separated by abut 3500 characters
        #Typically there will be 12 on each page, except the last page
        LISTING_LENGTH = 1000
        index = 0

        IDsIndex = []
        IDs = []

        while index < len(pretty_soup):
            index = pretty_soup.find('<div class="koi_sku">', index)
            if index == -1:
                break

            index = index+25
            index = pretty_soup.find('">', index)
            index = index + 2
            IDsIndex.append(index)
            end_index = pretty_soup.find('</a>', index)
            this_id = pretty_soup[index:end_index]
            IDs.append(str(this_id).strip())

            index = index + LISTING_LENGTH

        #check to see if this page is the same as the last one. If so,
        #we're done.
        if IDs == Last_Page_IDs:
            print('The previous page was the last one')
            break
        Last_Page_IDs=list(IDs)
        
        if len(IDs) != 16:
            print('Fewer than 16 IDs on this page:\nOK if this is the last page')  
        
        
        #For each ID, if it's already recorded, just check to see
        #if the final price should be updated
        #Else extract data and add to lists
        
        for idx,index in enumerate(IDsIndex):
            end_of_index = index + LISTING_LENGTH
            
            #If we have existing data, check for this ID
            already_recorded = False
            if 'prev_data' in locals():
                if IDs[idx] in prev_data['ID'].values:
                    already_recorded = True
            
            #If this ID exists, skip it
            if already_recorded == True:
                print('Skipping ID %s: already recorded' %IDs[idx])

            #If this ID doesn't exists, fill it in
            else:
                print('Working on ID %s' %IDs[idx])
                
                #Add ID to list
                ID.append(IDs[idx])
                
                #Get Type as string
                location_start = pretty_soup.find('"koi_info">', index, end_of_index)
                if location_start == -1:
                    Type.append([])
                else:
                    location_start += 11
                    location_start = pretty_soup.find('"', location_start, end_of_index)
                    location_start += 1
                    location_end = pretty_soup.find('</div>',location_start)
                    
                    this_type = pretty_soup[location_start:location_end].strip()
                    Type.append(this_type)
                    
                #Get Size as float (in cm)
                location_start = pretty_soup.find('"koi_info">', index, end_of_index)
                if location_end == -1:
                    Size.append([])
                else:            
                    location_start += 11
                    location_end = pretty_soup.find('"',location_start)
                    this_size = pretty_soup[location_start:location_end].strip()
                    #Check to see if this is a number
                    try:
                        this_size = float(this_size)
                        this_size = this_size * 2.54
                    except ValueError:
                        this_size = []
                    Size.append(this_size)
                    
                #Save picture as Champ[ID]
                this_ID = IDs[idx]
                file_name = 'ChampPics\Champ[' + str(this_ID) +'].jpg'
                jump_back = index - 300
                location_start = pretty_soup.find('http://champkoi.images', jump_back, index)
                if location_start == -1:
                    print('No picture for')
                else:
                    location_end = pretty_soup.find('"/>',location_start)
                    link = pretty_soup[location_start:location_end]
                    urllib.request.urlretrieve(link, file_name)
                    PicFile.append(file_name)
                
                #Get Buy it Now as float
                BuyItNow.append('[]')
                    
                #Add a price
                location_start = pretty_soup.find('<div class="price">',index, end_of_index)
                if location_start == -1:
                    FinalBid.append([])
                else:
                    #check for a strikethrough:
                        if pretty_soup.find('strike', index, end_of_index) >0: 
                            location_start = pretty_soup.find('</strike>', index, end_of_index)
                            
                        location_start = pretty_soup.find('</span>', location_start, end_of_index)
                        assert location_start>1
                        location_end = pretty_soup.find('</div>',location_start)
                        location_start += 7
                        this_final_bid = pretty_soup[location_start:location_end].strip()
                        #there might be a comma if it's more than $1,000:
                        this_final_bid = this_final_bid.replace(',','')
                        this_final_bid = float(this_final_bid)
                        FinalBid.append(this_final_bid)
            
                #No sex listed
                Sex.append('[]')  
                    
                #Get Breeder as string
                location_start = pretty_soup.find('Breeder:', index, end_of_index)
                location_start = pretty_soup.find('</span>', location_start,
                                                  end_of_index)
                if location_start == -1:
                    Breeder.append([])
                else:
                    location_end = pretty_soup.find('</div>',location_start)
                    location_start += 7
                    this_breeder = pretty_soup[location_start:location_end].strip()
                    Breeder.append(this_breeder)  
                    
                #Add todays date
                DateAdded.append(time.strftime('%Y_%m_%d'))
                
    #If this is the first time, create Pandas Dataframe with the information
    #otherwise add it to the existing file
    Champ = pd.DataFrame({'ID':ID,'Type':Type,
                               'BuyItNow':BuyItNow,'Size':Size,'Breeder':Breeder,
                               'Photo':PicFile, 'DateAdded':DateAdded, 'Sex':Sex,
                               'FinalBid':FinalBid})
    Champ['Website'] = 'Champ'
    if previous_data_file ==  '':
        file_name = ('Champ_' + time.strftime('%Y_%m_%d') + '.csv')
        Champ.to_csv(file_name, index=False)
    else:
        new_data_file = prev_data.append(Champ, ignore_index=True)
        file_name = ('Champ_' + time.strftime('%Y_%m_%d') + '.csv')
        new_data_file.to_csv(file_name, index=False)
        #move old file to archive
        archive_location = 'ChampOldFiles/' + previous_data_file
        os.rename(previous_data_file, archive_location)
        
        #Check that length of new data file is the same as the number of pictures:
        num_pictures = len(os.listdir('ChampPics'))        
        assert new_data_file.shape[0] == num_pictures, \
        'Number of rows in new data file not equal to number of pictures'
        
def DainichiImport(auction):
    
    #Find previous data file
    previous_data_file=('')
    for file in os.listdir(os.getcwd()):
        if file.startswith('Dainichi') & file.endswith('.csv'):
            previous_data_file=file
            prev_data=pd.read_csv(previous_data_file)
            break          

    ID = []
    Type = []
    PicFile = []
    BuyItNow = []
    FinalBid = []
    Size = []
    Sex = []
    Breeder = []
    DateAdded = []
    
    #Check that length of previous data file is the same as the number of pictures:
    num_pictures=len(os.listdir('DainichiPics'))        
    if previous_data_file !=  '':
        assert prev_data.shape[0] == num_pictures, \
        'Number of rows in existing data file not equal to number of pictures'
        
    Last_Page_IDs = []
    for i in range(1, 50):
        page=i
        url = 'http://ocs.sub.jp/na/list.php?AuctionNo=' + \
            str(auction) + '&category=&variety=&size_min=&size_max=&age=&sort=EntryNo&page=' + \
            str(page)
        print('Working on page %d of Dainichi' %page)
    
        r=requests.get(url, timeout=30)
        html_doc=r.text
        soup=BeautifulSoup(html_doc)
        pretty_soup=soup.prettify()
        
        #identify IDs on each page:
        #Assume IDs are listed as ID 12XXXX
        #Assume ID's are separated by abut 3500 characters
        #Typically there will be 12 on each page, except the last page
        LISTING_LENGTH = 50
        index = 0

        IDsIndex = []
        IDs = []
        pic_URLs = []
        #IDsIndex is the starting point of the url
        while index < len(pretty_soup):
            index = pretty_soup.find('./detail.php?auc=', index)
            if index == -1:
                break
            IDsIndex.append(index)
            index = pretty_soup.find('ent=', index)
            index = index + 4
            end_index = pretty_soup.find('">', index)
            this_id = pretty_soup[index:end_index]
            IDs.append(this_id)
            
            start_of_pic = pretty_soup.find('/uploads', index)
            end_of_pic = pretty_soup.find('.jpeg', start_of_pic)
            end_of_pic1 = pretty_soup.find('.jpg', start_of_pic)
            if end_of_pic == -1:
                end_of_pic = 10000000
            if end_of_pic1 == -1:
                end_of_pic1 = 10000000
            end = min(end_of_pic + 5, end_of_pic1 + 4)
            
            temp = pretty_soup[start_of_pic:end]
            pic_URLs.append('http://ocs.sub.jp/na' + temp)

            index = index + 50
        #check to see if this page is the same as the last one. If so,
        #we're done.
        if IDs == Last_Page_IDs:
            print('The previous page was the last one')
            break
        Last_Page_IDs=list(IDs)
        
        #For each ID, if it's already recorded, just check to see
        #if the final price should be updated
        #Else extract data and add to lists
        
        for idx,index in enumerate(IDsIndex):
            end_of_index = index + LISTING_LENGTH
            
            #If we have existing data, check for this ID
            already_recorded = False
            if 'prev_data' in locals():
                this_ID = 'auc_' + str(auction) + '_' + str(IDs[idx])
                if this_ID in prev_data['ID'].values:
                    already_recorded = True
            
            #If this ID exists, skip it
            if already_recorded == True:
                print('Skipping ID %s: already recorded' %IDs[idx])

            #If this ID doesn't exists, fill it in
            else:
                print('Working on ID %s' %IDs[idx])
                
                #Add ID to list
                ID.append(IDs[idx])
                
                #go to webpage for this fish
                page = 'http://ocs.sub.jp/na/detail.php?auc=' + str(auction) + \
                        '&ent=' + IDs[idx]
                r=requests.get(page, timeout=30)
                html_doc=r.text
                soup=BeautifulSoup(html_doc)
                pretty_soup=soup.prettify()
                
                #Get Type as string
                location_start = pretty_soup.find('Variety', 1)
                if location_start == -1:
                    Type.append([])
                else:
                    location_start = pretty_soup.find('info">', location_start)
                    location_start += 6
                    location_end = pretty_soup.find('</td>',location_start)
                    
                    this_type = pretty_soup[location_start:location_end].strip()
                    Type.append(this_type)
                    
                #Get Size as float (in cm)
                location_start = pretty_soup.find('Size', 1)
                if location_start == -1:
                    Size.append([])
                else:            
                    location_start = pretty_soup.find('-info">',location_start)
                    location_start += 7
                    location_end = pretty_soup.find('cm',location_start)
                    this_size = pretty_soup[location_start:location_end].strip()
                    #Check to see if this is a number
                    try:
                        this_size = float(this_size)
                        this_size = this_size
                    except ValueError:
                        this_size = []
                    Size.append(this_size)
                    
                #Save picture as Champ[ID]
                this_ID = IDs[idx]
                file_name = 'DainichiPics\Dainichi_auc'+str(auction)+'_[' + str(this_ID) +'].jpg'
                #link = 'http://ocs.sub.jp/na/uploads/' + str(auction) + '/' + str(this_ID) + '.jpeg'
                link = pic_URLs[idx]
                urllib.request.urlretrieve(link, file_name)
                PicFile.append(file_name)
                
                #Buy it Now is NA
                BuyItNow.append('[]')
                    
                #Price is NA
                FinalBid.append('[]')
            
                #Add sex
                location_start = pretty_soup.find('Gender', 1)
                location_start = pretty_soup.find('info">', location_start)
                if location_start == -1:
                    Sex.append([])
                else:
                    location_start += 6
                    location_end = pretty_soup.find('</td>',location_start)
                    this_breeder = pretty_soup[location_start:location_end].strip()
                    Sex.append(this_breeder)   
                    
                #Get Breeder as string
                Breeder.append('Dainichi')
                    
                #Add todays date
                DateAdded.append(time.strftime('%Y_%m_%d'))
                
    #If this is the first time, create Pandas Dataframe with the information
    #otherwise add it to the existing file
    Dainichi = pd.DataFrame({'ID':ID,'Type':Type,
                               'BuyItNow':BuyItNow,'Size':Size,'Breeder':Breeder,
                               'Photo':PicFile, 'DateAdded':DateAdded, 'Sex':Sex,
                               'FinalBid':FinalBid})
    Dainichi['Website'] = 'Dainichi'
    Dainichi['ID'] = Dainichi['ID'].apply(lambda x: 'auc_' + str(auction) + '_' + str(x))
    if previous_data_file ==  '':
        file_name = ('Dainichi_' + time.strftime('%Y_%m_%d') + '.csv')
        Dainichi.to_csv(file_name, index=False)
    else:
        new_data_file = prev_data.append(Dainichi, ignore_index=True)
        file_name = ('Dainichi_' + time.strftime('%Y_%m_%d') + '.csv')
        new_data_file.to_csv(file_name, index=False)
        #move old file to archive
        archive_location = 'DainichiOldFiles/' + previous_data_file
        os.rename(previous_data_file, archive_location)
        
        #Check that length of new data file is the same as the number of pictures:
        num_pictures = len(os.listdir('DainichiPics'))        
        assert new_data_file.shape[0] == num_pictures, \
        'Number of rows in new data file not equal to number of pictures'

def GenkiImport():
    
    #Find previous data file
    previous_data_file=('')
    for file in os.listdir(os.getcwd()):
        if file.startswith('Genki') & file.endswith('.csv'):
            previous_data_file=file
            prev_data=pd.read_csv(previous_data_file)
            break          

    ID = []
    Type = []
    PicFile = []
    BuyItNow = []
    FinalBid = []
    Size = []
    Sex = []
    Breeder = []
    DateAdded = []
    
    #Check that length of previous data file is the same as the number of pictures:
    num_pictures=len(os.listdir('GenkiPics'))        
    if previous_data_file !=  '':
        assert prev_data.shape[0] == num_pictures, \
        'Number of rows in existing data file not equal to number of pictures'
        
    Last_Page_IDs = []
    for i in range(1, 2):
        page=i
        url = 'http://www.genkikoi.com/SearchResults.asp?searching=Y&sort=13&cat=2052&show=160&page=' + \
            str(page)
        print('Working on page %d of Genki' %page)
    
        r=requests.get(url, timeout=30)
        html_doc=r.text
        soup=BeautifulSoup(html_doc)
        pretty_soup=soup.prettify()
        
        #identify IDs on each page:
        #Assume IDs are listed as ID 12XXXX
        #Assume ID's are separated by abut 3500 characters
        #Typically there will be 12 on each page, except the last page
        LISTING_LENGTH = 100
        index = 0

        IDsIndex = []
        IDs = []
        #IDsIndex is the starting point of the url without the backslash
        while index < len(pretty_soup):
            index = pretty_soup.find('colors_productname" href="', index)
            if index == -1:
                break
            index += 27
            IDsIndex.append(index)
            
            index = pretty_soup.find('itemprop="name">', index)
            index += 18
            end_index = pretty_soup.find('SOLD', index)  
            end_index_alt = pretty_soup.find('>', index)
            end_index = min (end_index, end_index_alt)
            this_id = pretty_soup[index:end_index].strip()
            IDs.append(this_id)
            
            #Sold out indicates this was a group:               
            sold_out = pretty_soup.find('OUT', end_index, end_index+10) > 0
            if sold_out == True:
                IDs.pop()
                IDsIndex.pop()

            index = index + 50
        #check to see if this page is the same as the last one. If so,
        #we're done.
        if IDs == Last_Page_IDs:
            print('The previous page was the last one')
            break
        Last_Page_IDs=list(IDs)
        
        #For each ID, if it's already recorded, just check to see
        #if the final price should be updated
        #Else extract data and add to lists
        
        for idx,index in enumerate(IDsIndex):
            end_of_index = index + LISTING_LENGTH
            
            #If we have existing data, check for this ID
            already_recorded = False
            if 'prev_data' in locals():
                if IDs[idx] in prev_data['ID'].values:
                    already_recorded = True
            
            #If this ID exists, skip it
            if already_recorded == True:
                print('Skipping ID %s: already recorded' %IDs[idx])

            #If this ID doesn't exists, fill it in
            else:
                print('Working on ID %s' %IDs[idx])
                
                #Add ID to list
                ID.append(IDs[idx])
                
                #go to webpage for this fish
                end_point = pretty_soup.find('" title=', index)
                end_url = pretty_soup[index:end_point]
                page = 'http://www.genkikoi.com/' + end_url
                
                r=requests.get(page, timeout=30)
                html_doc=r.text
                this_soup=BeautifulSoup(html_doc)
                this_pretty_soup=this_soup.prettify()
                
                #Get Type as string
                location_start = this_pretty_soup.find('title', 1)
                if location_start == -1:
                    Type.append([])
                else:
                    location_start += 7
                    location_end = this_pretty_soup.find('</title>',location_start)
                    
                    this_type = this_pretty_soup[location_start:location_end].strip()
                    Type.append(this_type)
                    
                #Get Breeder as string
                index = this_pretty_soup.find('<span id="product_description">', 1)
                location_start = this_pretty_soup.find('Breeder:', index, index + 100)
                if location_start == -1:
                    Breeder.append([])
                else:
                    location_start += 8
                    location_end = this_pretty_soup.find('<div>', location_start)
                    location_end_alt = this_pretty_soup.find('<br/>', location_start)
                    location_end = min(location_end, location_end_alt)
                    this_breeder = this_pretty_soup[location_start:location_end].strip()
                    Breeder.append(this_breeder)
                    
                #Get Size as float (in cm)
                location_start = this_pretty_soup.find('Size', location_end, 
                                                       location_end + 50)
                if location_start == -1:
                    Size.append([])
                else:            
                    location_start += 5
                    location_end = this_pretty_soup.find('inches', 20)
                    this_size = this_pretty_soup[location_start:location_end].strip()
                    #Check to see if this is a number
                    try:
                        this_size = float(this_size)
                        this_size = this_size * 2.54
                    except ValueError:
                        this_size = []
                    Size.append(this_size)
                
                #Add sex
                location_start = this_pretty_soup.find('Gender', location_start)
                if location_start == -1:
                    Sex.append([])
                else:
                    location_start += 7
                    location_end = this_pretty_soup.find('</div>',location_start)
                    location_end_alt = this_pretty_soup.find('<br/>',location_start)
                    location_end = min(location_end, location_end_alt)
                    this_gender = this_pretty_soup[location_start:location_end].strip()
                    Sex.append(this_gender)   
                    
                #Save picture as Genki[ID]
                this_ID = IDs[idx]
                temp = 'GenkiPics\Genki[' + str(this_ID) + '].jpg'
                file_name = temp.replace('"','')
                start = this_pretty_soup.find('http://www.genkikoi.com//v/vspfiles/photos',1)
                end = this_pretty_soup.find('"', start)
                link = this_pretty_soup[start:end]
                if start == -1:
                    start = this_pretty_soup.find('<a href="/v/vspfiles/photos',1)
                    start += 10
                    end = this_pretty_soup.find('"', start)
                    end_of_link = this_pretty_soup[start:end]
                    link = 'http://www.genkikoi.com/' + end_of_link
                try: 
                    urllib.request.urlretrieve(link, file_name)
                except OSError:
                    file_name='GenkiPics\\Genki[' + str(idx) +'].jpg'
                    urllib.request.urlretrieve(link, file_name)
                
                PicFile.append(file_name)
                
                #Buy it Now is NA
                BuyItNow.append('[]')
                    
                #Price is NA
                FinalBid.append('[]')
                    
                #Add todays date
                DateAdded.append(time.strftime('%Y_%m_%d'))
                
    #If this is the first time, create Pandas Dataframe with the information
    #otherwise add it to the existing file
    Genki = pd.DataFrame({'ID':ID,'Type':Type,
                               'BuyItNow':BuyItNow,'Size':Size,'Breeder':Breeder,
                               'Photo':PicFile, 'DateAdded':DateAdded, 'Sex':Sex,
                               'FinalBid':FinalBid})
    Genki['Website'] = 'Genki'
    
    if previous_data_file ==  '':
        file_name = ('Genki_' + time.strftime('%Y_%m_%d') + '.csv')
        Genki.to_csv(file_name, index=False)
    else:
        new_data_file = prev_data.append(Genki, ignore_index=True)
        file_name = ('Genki_' + time.strftime('%Y_%m_%d') + '.csv')
        new_data_file.to_csv(file_name, index=False)
        #move old file to archive
        archive_location = 'GenkiOldFiles/' + previous_data_file
        os.rename(previous_data_file, archive_location)
        
        #Check that length of new data file is the same as the number of pictures:
        num_pictures = len(os.listdir('GenkiPics'))        
        assert new_data_file.shape[0] == num_pictures, \
        'Number of rows in new data file not equal to number of pictures'
    
        