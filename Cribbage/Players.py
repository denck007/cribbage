from Cribbage.cribbage import cardIdToCountValue, cardIdToFaceValue

import numpy as np

class Player:
    '''
    Defines a type of player
    This is intended to be a parent class for all players
    The sub classes will implement the actual strategies
    '''

    def __init__(self,name):

        self.name = name
        self.resetHands()

    def resetHands(self):
        '''
        Reset the state of the players cards
        '''
        self.hand = None
        self.crib = None
        self.cardsPlayedMask = [False,False,False,False]

    def chooseHand(self,cardsDealt,isDealer):
        '''
        Player chooses what cards to keep in their hand and which to pass to the crib
        '''
        raise NotImplementedError("chooseHand must be implemented in subclass")

    def deal(self,deck,isDealer):
        '''
        Takes in deck and flag for if they are the dealer
        returns back the 2 cards they are passing to the crib
        '''
        raise NotImplementedError("deal must be implemented in subclass")

    def recieveCardsForCrib(self,cards):
        '''
        Take in cards from other player to be in this crib
        '''
        if self.crib is None:
            self.crib = cards
        else:
            self.crib.extend(cards)
    
    def playCard(self,cardsPlayed,cardsTotal,cardsSinceReset):
        '''
        return the next card to be played. 
        This function must return a card that brings the total to <= 31
        '''
        raise NotImplementedError("playCard must be implemented in subclass")

class RandomPlayer(Player):
    '''
    Player that makes random choices in the game
    '''

    def __init__(self,name):
        super().__init__(name)
    
    def deal(self,deck,isDealer,scorer=None):
        '''
        Draw a hand from the deck, then return a random 2 cards for the crib
        '''
        self.hand = deck.getCards(4)

        cardsForCrib = deck.getCards(2)
        if isDealer:
            self.recieveCardsForCrib(cardsForCrib)
            return None
        else:
            return cardsForCrib

    def playCard(self,cardsPlayed,cardsTotal,cardsSinceReset):
        '''
        Random player returns the next card that makes the total <= 31
        '''
        for idx in range(4):
            if self.cardsPlayedMask[idx]: # already played that card
                continue
            if cardIdToCountValue[self.hand[idx]] + cardsTotal <= 31:
                self.cardsPlayedMask[idx] = True
                return self.hand[idx]
            
        # unable to play any cards, return None to signal a Go
        return None

class Best4CardHandPlayer(RandomPlayer):
    '''
    Player chooses which cards to keep based on keeping the most points in
        their hand when putting cards into the crib
    Plays the cards in pegging randomly
    '''

    def deal(self,deck,isDealer,scorer):
        '''
        Draw a hand from the deck, then return a random 2 cards for the crib
        '''
        self.hand = deck.getCards(6)
        result = scorer.scorePossible4CardHand(self.hand)
        handIdxs = result['dropForBestHand'][:2]
        
        # debugging use only
        self._scorer_output = result
        self.originalDealtHand = self.hand.copy() # debug use only
        self.predictedScore = result['dropForBestHand'][-1]

        cardsForCrib = []
        cardsForCrib.append(self.hand.pop(max(handIdxs)))
        cardsForCrib.append(self.hand.pop(min(handIdxs)))
        if isDealer:
            self.recieveCardsForCrib(cardsForCrib)
            return None
        else:
            return cardsForCrib

class BestMinimalScorePlayer(RandomPlayer):
    '''
    Player starts by finding the best 4 cards to keep without consideration for the turn card.
        Then they find the hand that has a minimual improvement over this 4 card hand.
        The idea is that the worst case is a hand that matches the Best4CardHandPlayer.

    In reality this is choosing to keep the hand with the highest minimum score.
    '''
    def deal(self,deck,isDealer,scorer):
        self.hand = deck.getCards(6)

        result = scorer.scorePossible5CardHand(self.hand)
        handIdxs = result['dropForBestHand'][:2]
        
        # debugging use only
        self._scorer_output = result
        self.originalDealtHand = self.hand.copy() # debug use only
        self.predictedScore = result['dropForBestHand'][-1]

        cardsForCrib = []
        cardsForCrib.append(self.hand.pop(max(handIdxs)))
        cardsForCrib.append(self.hand.pop(min(handIdxs)))
        if isDealer:
            self.recieveCardsForCrib(cardsForCrib)
            return None
        else:
            return cardsForCrib 

class BestHandAndCribPlayer(RandomPlayer):
    '''
    This player chooses which cards to keep in their hand by:
        * Minimum score set by the points kept in their hand
        * Then find hand with best minimal improvement when the turn card is considered
        * Then consider what points they put in the crib (either as dealer or not)
            * This makes sure that if a kept hand tosses a pair to the other players
                crib that the net total is always better for themselves
            * As there will always be 0 scores in the crib, look at the average score for each crib
                and decide based on that
    '''

    def deal(self, deck, isDealer, scorer):

        self.hand = deck.getCards(6)

        # first find the hand with the best minimal score when considering the turn card
        handResult = scorer.scorePossible5CardHand(self.hand)
        cribResult = scorer.scorePossibleCribHands(self.hand)

        # If the player is the dealer then they get the crib, so the score adds to theirs,
        # If the other player is dealer we effectively loose those points
        if isDealer:
            minimumMap = handResult['mins'] + cribResult['scoreMap'].mean(axis=(-2,-1)).min()
        else:
            minimumMap = handResult['mins'] - cribResult['scoreMap'].mean(axis=(-2,-1)).min()

        sortedIdxsFlat = np.argsort(minimumMap.flatten())[:-15] # last 15 will always be masked off as np.NaN
        sortedIdxs = np.unravel_index(sortedIdxsFlat,minimumMap.shape)
        handIdxs = [sortedIdxs[0][-1],sortedIdxs[1][-1]]
        
        # debugging use only
        self._scorer_output = minimumMap # debug use only
        self.originalDealtHand = self.hand.copy() # debug use only
        self.predictedScore = minimumMap[sortedIdxs[0][-1],sortedIdxs[1][-1]] # debug use only

        cardsForCrib = []
        cardsForCrib.append(self.hand.pop(max(handIdxs)))
        cardsForCrib.append(self.hand.pop(min(handIdxs)))
        if isDealer:
            self.recieveCardsForCrib(cardsForCrib)
            return None
        else:
            return cardsForCrib
       
class ScorePeggingPlayer(RandomPlayer):
    '''
    Player trie to score the following:
    * Straights
    * 4 of a kind or 3 of a kind
    * 15s
    * 31
    * Pairs
    '''

    def playCard(self,cardsPlayed,cardsTotal,cardsSinceReset):
        '''
        Try to score the most points possible, so the order is 4 of a kind, largest possible straight, 3 of a kind, other straights, 15s, 31, then pairs
        '''
        valuesFacePlayed = [cardIdToFaceValue[cardId] for cardId in cardsPlayed][::-1] # want the order reversed to make it easier to iterate through
        #valuesFaceHand = [] # list of the face values in the hand that can be played
        #valuesCountHand = [] # list of the count values in the hand that can be played
        valuesFaceHandToIdxInHand = {} # map face value (number represeting numeric or J/Q/K/A) to index in hand
        valuesCountHandToIdxInHand = {} # map count value (A=1, J/Q/K=10) to index in hand
        for idx, cardId in enumerate(self.hand):
            valueFace = cardIdToFaceValue[cardId]
            valueCount = cardIdToCountValue[cardId]
            if self.cardsPlayedMask[idx]: # card has already been played
                continue
            elif valueCount + cardsTotal > 31: # cannot play card
                continue
            else:
                #valuesFaceHand.append(valueFace)
                #valuesCountHand.append(valueCount)
                valuesFaceHandToIdxInHand[valueFace] = cardId
                valuesCountHandToIdxInHand[valueCount] = cardId
            
        if len(valuesCountHandToIdxInHand) == 0: # cannot play anything, so 'Go'
            return None
        
        # Check for pairs
        playedMatching = 1 # kind of wierd, Tracks the number of cards matching the last layed card and the last layed card matches itself
        cardForPair = None
        for idx in range(cardsSinceReset-1):
            if valuesFacePlayed[idx] == valuesFacePlayed[idx+1]:
                if playedMatching == 1: # first match, so set values
                    playedMatching = 2
                    cardForPair = valuesFacePlayed[idx]
                else:
                    playedMatching += 1
            else:
                break
        
        # check for straights
        playedStraight = -1
        cardForStraight = None
        for idx in range(cardsSinceReset-1):
            if valuesFacePlayed[idx] == (valuesFacePlayed[idx+1]+1):
                if playedStraight < 0:
                    playedStraight = 2 # first match gives a run of 2
                    cardForStraight = valuesFacePlayed[idx] + 1 # a run of 2 exists, so set the required card to continue the straight
                else:
                    playedStraight += 1 # subsequent matchs add to the length of the run                    
            else:
                break
    
        if cardsTotal < 15:
            cardFor15 = 15 - cardsTotal
        else:
            cardFor15 = None
        
        cardFor31 = 31 - cardsTotal # may result in a non-existant card
        
        # Now go through the cases in order of decreasing points and see if the conditions are right to score
        if playedMatching == 3 and (cardForPair in valuesFaceHandToIdxInHand): # can make 4 of a kind, 3 of a kind is worth 12
            cardId = valuesFaceHandToIdxInHand[cardForPair]
            
        elif playedStraight == 7 and (cardForStraight in valuesFaceHandToIdxInHand): # can make a straight of any length, minimum value is 3, max is 5 (A,2,3,4,5,6,7)
            cardId = valuesFaceHandToIdxInHand[cardForStraight]
        
        elif playedMatching == 2 and (cardForPair in valuesFaceHandToIdxInHand): # can make 3 of a kind, 3 of a kind is worth 6
            cardId = valuesFaceHandToIdxInHand[cardForPair]
        
        elif playedStraight >= 2 and (cardForStraight in valuesFaceHandToIdxInHand): # can make a straight between 3 and 6, worth 3-6 points
            cardId = valuesFaceHandToIdxInHand[cardForStraight]

        elif playedMatching == 1 and (cardForPair in valuesFaceHandToIdxInHand): # can make a pair for 2
            cardId = valuesFaceHandToIdxInHand[cardForPair]
            
        elif cardFor15 in valuesCountHandToIdxInHand: # can make a 15
            cardId = valuesCountHandToIdxInHand[cardFor15]

        elif cardFor31 in valuesCountHandToIdxInHand:   # can make 31
            cardId = valuesCountHandToIdxInHand[cardFor31]

        else:   # no points can be scored, play a random card
            cardId = valuesCountHandToIdxInHand[list(valuesCountHandToIdxInHand)[0]] # get the first card in the hand

        idx = self.hand.index(cardId) # get the index in the hand of the card to play
        self.cardsPlayedMask[idx] = True # mark as played
        return self.hand[idx]

class BestHandAndCribAndScorePeggingPlayer(RandomPlayer):
    '''
    Combines the ScorePegging player and the BestMinimalScorePlayer
    '''

    def deal(self,deck,isDealer,scorer):
        self.hand = deck.getCards(6)

        result = scorer.scorePossible5CardHand(self.hand)
        handIdxs = result['dropForBestHand'][:2]
        
        # debugging use only
        self._scorer_output = result
        self.originalDealtHand = self.hand.copy() # debug use only
        self.predictedScore = result['dropForBestHand'][-1]

        cardsForCrib = []
        cardsForCrib.append(self.hand.pop(max(handIdxs)))
        cardsForCrib.append(self.hand.pop(min(handIdxs)))
        if isDealer:
            self.recieveCardsForCrib(cardsForCrib)
            return None
        else:
            return cardsForCrib 
       
    def playCard(self,cardsPlayed,cardsTotal,cardsSinceReset):
        '''
        Try to score the most points possible, so the order is 4 of a kind, largest possible straight, 3 of a kind, other straights, 15s, 31, then pairs
        '''
        valuesFacePlayed = [cardIdToFaceValue[cardId] for cardId in cardsPlayed][::-1] # want the order reversed to make it easier to iterate through
        #valuesFaceHand = [] # list of the face values in the hand that can be played
        #valuesCountHand = [] # list of the count values in the hand that can be played
        valuesFaceHandToIdxInHand = {} # map face value (number represeting numeric or J/Q/K/A) to index in hand
        valuesCountHandToIdxInHand = {} # map count value (A=1, J/Q/K=10) to index in hand
        for idx, cardId in enumerate(self.hand):
            valueFace = cardIdToFaceValue[cardId]
            valueCount = cardIdToCountValue[cardId]
            if self.cardsPlayedMask[idx]: # card has already been played
                continue
            elif valueCount + cardsTotal > 31: # cannot play card
                continue
            else:
                #valuesFaceHand.append(valueFace)
                #valuesCountHand.append(valueCount)
                valuesFaceHandToIdxInHand[valueFace] = cardId
                valuesCountHandToIdxInHand[valueCount] = cardId
            
        if len(valuesCountHandToIdxInHand) == 0: # cannot play anything, so 'Go'
            return None
        
        # Check for pairs
        playedMatching = 1 # kind of wierd, Tracks the number of cards matching the last layed card and the last layed card matches itself
        cardForPair = None
        for idx in range(cardsSinceReset-1):
            if valuesFacePlayed[idx] == valuesFacePlayed[idx+1]:
                if playedMatching == 1: # first match, so set values
                    playedMatching = 2
                    cardForPair = valuesFacePlayed[idx]
                else:
                    playedMatching += 1
            else:
                break
        
        # check for straights
        playedStraight = -1
        cardForStraight = None
        for idx in range(cardsSinceReset-1):
            if valuesFacePlayed[idx] == (valuesFacePlayed[idx+1]+1):
                if playedStraight < 0:
                    playedStraight = 2 # first match gives a run of 2
                    cardForStraight = valuesFacePlayed[idx] + 1 # a run of 2 exists, so set the required card to continue the straight
                else:
                    playedStraight += 1 # subsequent matchs add to the length of the run                    
            else:
                break
    
        if cardsTotal < 15:
            cardFor15 = 15 - cardsTotal
        else:
            cardFor15 = None
        
        cardFor31 = 31 - cardsTotal # may result in a non-existant card
        
        # Now go through the cases in order of decreasing points and see if the conditions are right to score
        if playedMatching == 3 and (cardForPair in valuesFaceHandToIdxInHand): # can make 4 of a kind, 3 of a kind is worth 12
            cardId = valuesFaceHandToIdxInHand[cardForPair]
            
        elif playedStraight == 7 and (cardForStraight in valuesFaceHandToIdxInHand): # can make a straight of any length, minimum value is 3, max is 5 (A,2,3,4,5,6,7)
            cardId = valuesFaceHandToIdxInHand[cardForStraight]
        
        elif playedMatching == 2 and (cardForPair in valuesFaceHandToIdxInHand): # can make 3 of a kind, 3 of a kind is worth 6
            cardId = valuesFaceHandToIdxInHand[cardForPair]
        
        elif playedStraight >= 2 and (cardForStraight in valuesFaceHandToIdxInHand): # can make a straight between 3 and 6, worth 3-6 points
            cardId = valuesFaceHandToIdxInHand[cardForStraight]

        elif playedMatching == 1 and (cardForPair in valuesFaceHandToIdxInHand): # can make a pair for 2
            cardId = valuesFaceHandToIdxInHand[cardForPair]
            
        elif cardFor15 in valuesCountHandToIdxInHand: # can make a 15
            cardId = valuesCountHandToIdxInHand[cardFor15]

        elif cardFor31 in valuesCountHandToIdxInHand:   # can make 31
            cardId = valuesCountHandToIdxInHand[cardFor31]

        else:   # no points can be scored, play a random card
            cardId = valuesCountHandToIdxInHand[list(valuesCountHandToIdxInHand)[0]] # get the first card in the hand

        idx = self.hand.index(cardId) # get the index in the hand of the card to play
        self.cardsPlayedMask[idx] = True # mark as played
        return self.hand[idx]

