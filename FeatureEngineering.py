# -*- coding: utf-8 -*-
"""
Created on Wed Aug  9 14:19:27 2017

@author: clorja
"""

import pandas as pd
import os
import numpy as np
import cv2
import random
import itertools
import time
import importlib
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt

import CNN
import Inception
import Xception
import EvaluatePredictions

importlib.reload(CNN)
importlib.reload(Xception)
importlib.reload(EvaluatePredictions)
importlib.reload(Inception)

Resize_ratio = 3
Base_width = 265
Base_height = 428
Resized_width = int(Base_width / Resize_ratio)
Resized_height = int(Base_height / Resize_ratio)

#Resized_width = 71
#Resized_height = 71

KoiTypes={0 : 'other',
          1 : 'Sanke',
          2 : 'Shiro Utsuri',
          3 : 'Showa',
          4 : 'Kohaku',
          5 : 'Ginrin Showa',
          6 : 'Tancho Kohaku',
          7 : 'Ki Utsuri',
          8 : 'Ginrin Shiro Utsuri',
          9 : 'Ginrin Kohaku',
          10: 'Kujyaku',
          11: 'Kikokuryu'}

KoiTypes={0 : 'other',
          1 : 'Male',
          2 : 'Female'}

def run(filepath=None, image_aug=False):
    #import pre-processed split data.
    #run model
    #evaluate and display results
    
    #filepath is where to save the model and weights
    
    start = time.time()
    (X_train, X_test, y_train, y_test, train_pics, test_pics,
           train_pics_original, test_pics_original) = setup(Resized_height, Resized_width)
    
    model = Xception.create_model(train_pics, test_pics, y_train, y_test,
                                  Resized_height, Resized_width, image_aug)
    
    run_time_min = (time.time()-start) / 60
    print('\nProcessing took %2.1f minutes' %run_time_min )
    
    if filepath is not  None:
        model.save(filepath)
        full_path = os.getcwd() + '\\' + filepath
        print('Model saved to %s' %full_path)
        
    test_predictions_prob = model.predict(test_pics)
    #return(test_predictions_prob, X_test, y_test, test_pics_original, KoiTypes)
    
    #draw confusion matrix
    EvaluatePredictions.koi_confusion_matrix(y_test, test_predictions_prob, 
                                             KoiTypes, normalize = False)
    EvaluatePredictions.koi_confusion_matrix(y_test, test_predictions_prob, 
                                             KoiTypes, normalize = True)
    
    #select 24 random test points and display them
    test_size = test_predictions_prob.shape[0]
    to_display = random.sample(range(0,test_size), (24))
    test_predictions_prob_dis = test_predictions_prob[to_display]
    test_pics_original_dis = test_pics_original[to_display,:,:,:]
    y_test_dis = y_test.iloc[to_display]
    X_test_dis = X_test.iloc[to_display,:]
    EvaluatePredictions.display_results(test_predictions_prob_dis, test_pics_original_dis, KoiTypes, 
                                        y_test_dis, X_test_dis)
    return(X_train, X_test, y_train, y_test)
def setup(IMAGE_SIZE_H, IMAGE_SIZE_W):
    #load data, define test/training split, load pictures, perform 
    #pre-processing
    data=ProcessData()
    
    #temp change to not have any unknowns
    data=data[data['type_enum']>0]
    
    #Define test/training split
    test_amount = 0.10    
    X_train, X_test, y_train, y_test = train_test_split(
            data, data['type_enum'], test_size=test_amount)
    
    #Load images
    print('Processing training images')
    train_pics=prep_images(X_train['Photo'], IMAGE_SIZE_H, IMAGE_SIZE_W)
    print('Processing test images')
    test_pics=prep_images(X_test['Photo'], IMAGE_SIZE_H, IMAGE_SIZE_W)
    
    train_pics_original = np.copy(train_pics)
    test_pics_original = np.copy(test_pics)
    
    #normalization and preprocessing
    train_pics = train_pics/255
    test_pics = test_pics/255
    
    return(X_train, X_test, y_train, y_test, train_pics,test_pics,
           train_pics_original, test_pics_original)

def ProcessData():
    #Imports spreadsheets and adds columns for
    #Kohaku, Tancho, Ginrin
    list_of_sheets=['Kodama', 'Kloubec', 'Champ', 'Dainichi', 'Manual']
    folder_with_sheets = 'WebScraping'
    dfs=[]
    
    list_of_files = os.listdir(folder_with_sheets)
    
    for file_name in list_of_sheets:
        for file in list_of_files:
            if file.startswith(file_name) & file.endswith('.csv'):
                this_file = os.path.join(folder_with_sheets, file)
                dfs.append(pd.read_csv(this_file))
                break     
    
    assert len(dfs)>0 , 'No data files found'
    data = pd.concat(dfs)
    
    """
    KoiTypes={0 : 'other',
              1 : 'Sanke',
              2 : 'Shiro Utsuri',
              3 : 'Showa',
              4 : 'Kohaku',
              5 : 'Ginrin Showa',
              6 : 'Tancho Kohaku',
              7 : 'Ki Utsuri',
              8 : 'Ginrin Shiro Utsuri',
              9 : 'Ginrin Kohaku',
              10: 'Kujyaku',
              11: 'Kikokuryu'}
    """    
    def basic_type(text):
#        if 'Sanke' in text:
#            return(1)
#        
#        elif 'Ginrin Shiro Utsuri' in text:
#            return(8)
#        elif 'Shiro Utsuri' in text:
#            return(2)
#        
#        elif 'Ginrin Showa' in text:
#            return(5)
#        elif 'Showa' in text:
#            return(3)
#        
#        elif 'Tancho Kohaku' in text:
#            return(6)
#        elif 'Ginrin Kohaku' in text:
#            return(9)
#        elif 'Kohaku' in text:
#            return(4)
#        
#        elif 'Ki Utsuri' in text:
#            return(7)
#        
#        elif 'Kujyaku' in text:
#            return(10)
#        
#        elif 'Kikokuryu' in text:
#            return(11)
        if 'Male' in text:
            return(1)
        elif 'Female' in text:
            return (2)
        
        else: return(0)
        
    #data['type_enum'] = data['Type'].apply(basic_type)
    data['type_enum'] = data['Sex'].apply(basic_type)
    
    return (data)
    

def read_image(file_path, IMAGE_SIZE_H, IMAGE_SIZE_W):
    img = cv2.imread(file_path, cv2.IMREAD_COLOR) #cv2.IMREAD_GRAYSCALE
    
    """
    #Need to fix resizing?
    if (img.shape[0] >= img.shape[1]): # height is greater than width
       resizeto = (IMAGE_SIZE, int (round (IMAGE_SIZE * (float (img.shape[1])  / img.shape[0]))));
    else:
       resizeto = (int (round (IMAGE_SIZE * (float (img.shape[0])  / img.shape[1]))), IMAGE_SIZE);
    #img2 = cv2.resize(img, (resizeto[1], resizeto[0]), interpolation=cv2.INTER_CUBIC)
    img2 = cv2.resize(img, (IMAGE_SIZE_W, IMAGE_SIZE_H), interpolation=cv2.INTER_CUBIC)
    
    img3 = cv2.copyMakeBorder(img2, 0, IMAGE_SIZE - img2.shape[0], 0, IMAGE_SIZE - img2.shape[1], cv2.BORDER_CONSTANT, 0)
    """   
    img3=cv2.resize(img,(IMAGE_SIZE_W, IMAGE_SIZE_H),interpolation=cv2.INTER_CUBIC)
    #changed this up
    return (img3[:,:,::-1])   # turn into rgb format

def prep_images(images, IMAGE_SIZE_H, IMAGE_SIZE_W):
    #goes through a list-like structure of images and calls read_image for each
    #Use the list of images in the spreadsheet to ensure consistency between
    #the images and the data
    #Output is an array of (n, image_h, image_w, 3)
    
    CHANNELS = 3
    #pixel_depth = 255.0  # Number of levels per pixel.
    
    count = len(images)
    
    #changed this up
    data = np.ndarray((count, IMAGE_SIZE_H, IMAGE_SIZE_W, CHANNELS), dtype=np.uint8)
    #data = np.ndarray((count, IMAGE_SIZE, IMAGE_SIZE, CHANNELS), dtype=np.float32)

    for i, image_file in enumerate(images):
        image_file = os.path.join('WebScraping', image_file)
        image = read_image(image_file, IMAGE_SIZE_H, IMAGE_SIZE_W)
        #changed this up
        image_data=image
        #image_data = np.array (image, dtype=np.float32);
        
        #image_data[:,:,0] = (image_data[:,:,0].astype(float) - pixel_depth / 2) / pixel_depth
        #image_data[:,:,1] = (image_data[:,:,1].astype(float) - pixel_depth / 2) / pixel_depth
        #image_data[:,:,2] = (image_data[:,:,2].astype(float) - pixel_depth / 2) / pixel_depth
        
        data[i] = image_data; # image_data.T
        if i%250 == 0: print('Processed {} of {}'.format(i, count)) 
        
    """
    to test image:    
    import matplotlib.pyplot as plt
    import matplotlib.image as mpimg
    plt.imshow(images[0])
    """
    return data

def plot_confusion_matrix(cm, classes,
                          normalize=False,
                          title='Confusion matrix',
                          cmap=plt.cm.Blues):
    """
    This function prints and plots the confusion matrix.
    Normalization can be applied by setting `normalize=True`.
    """
    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        #print("Normalized confusion matrix")
    #else:
        #print('Confusion matrix, without normalization')

    #print(cm)

    plt.figure()
    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    plt.title(title)
    plt.colorbar()
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes, rotation=45)
    plt.yticks(tick_marks, classes)

    fmt = '.2f' if normalize else 'd'
    thresh = cm.max() / 2.
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j, i, format(cm[i, j], fmt),
                 horizontalalignment="center",
                 color="white" if cm[i, j] > thresh else "black")

    plt.tight_layout()
    plt.ylabel('True label')
    plt.xlabel('Predicted label')
    

    
    
         