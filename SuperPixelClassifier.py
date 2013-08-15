import numpy as np

import scipy.stats

import pomio



# Create a random forest classifier for superpixel class given observed image features
# 1) Get labelled training data
# 2) Create single training dataset for each superpixel in each training image:    trainingData = [superPixelFeatures , superPixelLabels]
# 3) Create random forest classifier from data
# 4) Save classifier to file


def getSuperPixelTrainingData(msrcDataDirectory, scale):
    # Should probably make this a call to pomio in case the ordering changes in the future...
    voidClassLabel = 13
    
    # These could be user-specified
    if scale == None:
        scale = 0.1 # default to 10% of data
        
    numSuperPixels = 400
    superPixelCompactness = 10
    
    msrcData = pomio.msrc_loadImages(msrcDataDirectory)

    print "Now generating superpixel random forest classifier for MSRC data"
    
        
    splitData = pomio.splitInputDataset_msrcData(msrcData,
            datasetScale=scale,
            keepClassDistForTraining=True,
            trainSplit=0.6,
            validationSplit=0.2,
            testSplit=0.2
            )
    
    # prepare superpixel training data
    
    # for each image:
    #   determine superpixel label (discard if void)
    #   compute superpixel features of valid superpixels
    #   append features to cumulative array of all super pixel features
    #   append label to array of all labels
    
    
    trainingMsrcImages = splitData[0]
    
    numberTrainingImages = np.shape(trainingMsrcImages)[0]
    
    superPixelTrainFeatures = None
    superPixelTrainLabels = np.array([], int) # used for superpixel labels
    superPixelIgnoreList = np.array([], int) # this is used to skip over the superpixel in feature processing
    
    numberVoidSuperPixels = 0
    
    for imgIdx in range(0, numberTrainingImages):
    
        # get raw image and ground truth labels
        img = trainingMsrcImages[imgIdx].m_img
        imgPixelLabels = trainingMsrcImages[imgIdx].m_gt
        
        # create superpixel map for image
        superPixelMap = SuperPixels.getSuperPixels_SLIC(img, numberSuperPixels, superPixelCompactness)
        numberSuperPixels = np.unique(superPixelMap)
    
        # create superpixel exclude list & superpixel label array
        for spIdx in range(0, numberSuperPixels):
        
            # Assume superpisel labels are sequence of integers
            superPixelValueMask = (superPixelMask == spIdx) # Boolean array for indexing superpixel-pixels
            superPixelLabel = this.assignClassLabelToSuperPixel(superPixelValueMask, imgPixelLabels)
            
            if(superPixelLabel == voidClassLabel):
                # add to ignore list, increment void count & do not add to superpixel label array
                superPixelIgnoreList = np.append(superPixelIgnoreList, spIdx)
                numberVoidSuperPixels = numberVoidSuperPixels + 1
                
            else:
            
                superPixelTrainLabels = np.append(superPixelTrainLabels, superPixelLabel)
                
        # Now we have the superpixel labels, and an ignore list of void superpixels - time to get the features!
        imgSuperPixelFeatures = FeatureGenerator.generateSuperPixelFeatures(img, superPixelMap, excludeSuperPixelList=superPixelIgnoreList)
        
        if superPixelTrainFeatures == None:        
            superPixelTrainFeatures = imgSuperPixelFeatures;
        else:
            # stack the superpixel features into a single list
            superPixelTrainFeatures = np.vstack( [ superPixeTrainFeatures, imgSuperPixelFeatures ] )
    
    print "Total superpixels =" , numberSuperPixels
    print "Total void superpixels =" , numberVoidSuperPixels
    numberValidSuperPixels = (numberSuperPixels - numberVoidSuperPixels)
    print "Total valid superpixels for training =" , numberValidSuperPixels
    
    assert np.shape(superPixelTrainLabels)[0] == numberValidPixels,\
            ("The number of training superpixel labels (" + str(np.shape(superPixelTrainLabels)[0]) + " != number of valid superpixels! (" + str(numberValidSuperPixels) + ").")
    
    assert np.shape(superPixelTrainFeatures)[0] == numberValidPixels, \
            ("The number of training superpixel features (" + str(np.shape(superPixelTrainFeatures)[0]) + " != number of valid superpixels! (" + str(numberValidSuperPixels) + ").")
    
    return [ superPixelTrainFeatures, superPixelTrainLabels ]
    
    


# Could use other params e.g. training dataset size
def createSuperPixelRandomForestClassifier(msrcDataDirectory, classifierDirectory):

    # Get training data
    superPixelTrainData = getSuperPixelTrainingData(msrcDataDirectory, scale)
    superPixelTrainFeatures = superPixelTrainData[0]
    superPixelTrainLabels = superPixelTrainData[1]
    
    # now train random forest classifier on labelled superpixel data
    print '**Training a random forest on %d examples...' % len(superPixelTrainLabels)
    print 'Labels represented: ', np.unique( labvec )

    numEstimators = 100
    
    classifier = sklearn.ensemble.RandomForestClassifier(n_estimators=numEstimators)
    classifier = classifier.fit( superPixelTrainData, superPixelTrainLabels)
    
    # Now serialise the classifier to file
    classifierFilename = classifierDirectory + "/" + "randForest_superPixel_nEst" + str(numEstimators) + ".pkl"
    
    pomio.pickleObject(classifier, classifierFilename)
    
    print "Rand forest classifier saved @ " + str(classifierFilename)
    



def assignClassLabelToSuperPixel(superPixelValueMask, imagePixelLabels):
    """This function provides basic logic for setting the overall class label for a superpixel"""
    
    # just adopt the most frequently occurring class label as the superpixel label
    
    #>>> aFreq = stats.itemfreq(a) - use as we dont expect very large sets of class labels in super pixel, upper limit is number of classes and superpixel pixel instances
    #>>> maxFreq = np.max(aFreq[:,1])
    #>>> maxTerm = (aFreq[:,1] == maxFreq)
    
    superPixelConstituentLabels = imagePixelLabels[superPixelValueMask]
    
    labelCount = stats.itemfreq(superPixelConstituentLabels)
    
    maxLabelFreq = np.max(labelCount[:, 1])
    
    maxLabel = (labelCount[:,1] == maxLabelFreq)
    
    # what if the max count gives more than 1 match?  Naughty superpixel.
    # It would be nice to select the class that is least represented in the dataset so far...
    if np.shape(maxLabel) > 1:
        print "\tWARN: More than 1 class label have an equal maximal count in the superpixel: {" , maxLabel[:,0] , "}"
        print "\tWARN: Will return the first non-void label."
    
        for idx in range(0, np.shape(maxLabel)[0]):
            # void class label = 13
            if maxLabel[idx,0] != 13:
                # return the first non-void label in the array of max labels
                return maxLabel[idx,0]
                
    else:
        # if the max label is void, issue a warning; assume filtered out in processing step
        if maxLabel[0,0] == 13:
            print "\tWARN: The most frequent label in the superpixel is void; should discard this superpixel by adding to exclude list."
            
        return maxLabel[0,0]
