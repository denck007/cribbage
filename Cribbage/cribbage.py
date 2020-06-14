import random
import sys
import time

import numpy as np
from itertools import combinations

cardIdToName = [" A"," 2"," 3"," 4"," 5"," 6"," 7"," 8"," 9"," 10"," J"," Q", " K"]*4
cardIdToSuiteName = ["H"]*13
cardIdToSuiteName.extend(["D"]*13)
cardIdToSuiteName.extend(["C"]*13)
cardIdToSuiteName.extend(["S"]*13)
cardIdToSuite = []
cardIdToFaceValue = []
cardIdToCountValue = []

for cardId in range(52):
    suite = cardId//13
    faceValue = cardId - suite*13 + 1
    countValue = min(faceValue,10)
    cardIdToSuite.append(suite)
    cardIdToFaceValue.append(faceValue)
    cardIdToCountValue.append(countValue)

def printCards(cardIds,showSuite=True):
    '''
    Given a list of cardIds, return a string with the face value and optional suite
    '''
    out = ""
    for cardId in cardIds:
        if showSuite:
            out += "{:3s}{} ".format(cardIdToName[cardId],cardIdToSuiteName[cardId])
        else:
            out += "{:4s} ".format(cardIdToName[cardId])
    return out
    
class Hand:
    '''
    Defines a players hand
    '''

    def __init__(self, deck, isCrib=False):
        '''
        deck: Instance of the deck class to draw the cards from
        isCrib: bool, if the hand is for the crib
        '''
        self.isCrib = isCrib

        if isCrib:
            self.cards = []
        else:
            self.cards = deck.getCards(count=6)
     

        









