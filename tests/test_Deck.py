from unittest import TestCase
from Cribbage.cribbage import Deck, Hand, HandScorer
import numpy as np

class test_Deck(TestCase):
    def test_getCards(self):
        '''
        Test that the correct number of cards are returned
        Test that no duplicates are retured
        '''

        deck = Deck()

        # verify 1 card is drawn properly
        drawnCards = deck.getCards(1)
        self.assertEqual(len(drawnCards),1) 
        # verify multiple cards drawn properly
        drawnCards.extend(deck.getCards(5))
        self.assertEqual(len(drawnCards),6) 

        # verify the correct number of cards are still in the deck
        self.assertEqual(len(deck.cards),46)

        drawnCards.extend(deck.getCards(46))
        self.assertEqual(sorted(drawnCards),list(set(drawnCards)))
    
    def test_cardIdTo(self):

        deck = Deck()

        cards = list(range(52))
        suites = [0]*13 + [1]*13 + [2]*13 + [3]*13
        faceValues = list(range(1,13+1))*4
        countValues = list(range(1,10+1)) + [10]*3
        countValues.extend(countValues)
        countValues.extend(countValues)

        self.assertEqual(deck.cardIdsToCountValue(cards),countValues)
        self.assertEqual(deck.cardIdsToFaceValue(cards),faceValues)
        self.assertEqual(deck.cardIdsToSuites(cards),suites)
