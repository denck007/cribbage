import random
from Cribbage.cribbage import cardIdToSuite,cardIdToFaceValue,cardIdToCountValue

class Deck:
    '''
    Define a deck of cards, return hands, pull individual cards

    Cards are represented by integers 0-52.
    Suite: 
        * suite = cardId//13
    Face Value:
        * Is the value used to count runs and pairs
        * faceValue = cardId - suite*13 + 1
    Count Value:
        * Is value used to count 15s, face cards are all use value of 10
        * countValue = min(faceValue,10)
    '''

    def __init__(self):
        '''
        Create a deck of cards in a random order
        '''
        self.shuffle()

    def shuffle(self):
        '''
        shuffle the cards
        '''
        self.cards = list(range(52))
        random.shuffle(self.cards)
    
    def getCards(self,count):
        '''
        Return a list of cards drawn from the deck
        '''
        return [self.cards.pop() for item in range(count)]

    def cardIdsToSuites(self,cardIds):
        '''
        Takes in a list of card ids and returns a list of corresponding suits
        '''
        values = []
        for cardId in cardIds:
            values.append(cardIdToSuite[cardId])
        return values

    def cardIdsToFaceValue(self,cardIds):
        '''
        Takes a list of card ids and returns list of corresponding face values
        '''
        values = []
        for cardId in cardIds:
            values.append(cardIdToFaceValue[cardId])
        return values

    def cardIdsToCountValue(self,cardIds):
        '''
        Takes a list of card ids and returns list of corresponding count values
        '''
        values = []
        for cardId in cardIds:
            values.append(cardIdToCountValue[cardId])
        return values
