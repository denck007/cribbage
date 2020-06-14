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
    
class CribbageException(Exception):
    '''
    Base class for cribbage exceptions
    '''
    pass

class EndOfGameException(CribbageException):
    '''
    Raised when the game is won
    '''
    def __init__(self, winner, winnerScore, looser, looserScore):
        self.message = "{} defeated {} with a score of {:3d} to {:3d}".format(winner,
                                                                        looser,
                                                                        winnerScore,
                                                                        looserScore)

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
     
class HandScorer:
    '''
    Returns the score of a hand
    Caches results so that scores are only computed once
        * Cache size is 52^5, but will only fill 52*51*50*49*52 spots at max
            because the hand is sorted before checking the cache. this removes
            the cases where the same hand is given, but in a different order
    '''

    def __init__(self,useCacheLarge=False,useCache15=True,useCachePair=True,useCacheStraight=True):
        
        self.useCacheLarge = useCacheLarge
        self.useCache15 = useCache15
        self.useCachePair = useCachePair
        self.useCacheStraight = useCacheStraight

        if self.useCacheLarge:
            self.scores = np.empty((52,52,52,52,52),dtype=np.int8)
            self.scores.fill(-1)
            self.scores_4card = np.empty((52,52,52,52),dtype=np.int8)
            self.scores_4card.fill(-1)

        if self.useCache15:
            self.scores_15s = np.empty((11,11,11,11,11),dtype=np.int8)
            self.scores_15s.fill(-1)
            self.scores_15s_4card = np.empty((11,11,11,11),dtype=np.int8)
            self.scores_15s_4card.fill(-1)
    
        if self.useCachePair:
            self.scores_pairs = np.empty((14,14,14,14,14),dtype=np.int8)
            self.scores_pairs.fill(-1)
            self.scores_pairs_4card = np.empty((14,14,14,14),dtype=np.int8)
            self.scores_pairs_4card.fill(-1)

        if self.useCacheStraight:
            self.scores_straight = np.empty((14,14,14,14,14),dtype=np.int8)
            self.scores_straight.fill(-1)
            self.scores_straight_4card = np.empty((14,14,14,14),dtype=np.int8)
            self.scores_straight_4card.fill(-1)

    def __call__(self,cardsInHand,turnCard):
        '''
        Return the score of the hand
            * This is made up of the cards in the players hand (4 cards)
                plus the turn card. It is important to keep them seperate
                for the case of flushes and knobs
        cardsInHand: list<int>, list of the 4 cardIds in the hand
        turnCard: int, the cardId for the turn card
        Checks to see if it has already been computed and cached, then computes if needed
        ''' 
        # the score can vary based on weather a card is in the hand or is the turn card,
        #   so keeping the order is important
        allCards = sorted(cardsInHand)
        allCards.append(turnCard) 
        
        # only need values for debugging
        #values = [cardIdToFaceValue[card] for card in allCards]
        #print("\n----\nHand: {}\nValue: {}\n----".format(allCards,values))
        
        # first check the cache
        if self.useCacheLarge and (len(allCards) == 5):
            if self.scores.item(*allCards) != -1:
                return self.scores.item(*allCards)
        elif self.useCacheLarge and (len(allCards) == 4):
            if self.scores_4card.item(*allCards) != -1:
                return self.scores_4card.item(*allCards)

        # did not find data in the cache, so compute the score
        score = 0
        score += self.score15s(cardsInHand,turnCard)
        #print("\n\tScore after 15s:      {}".format(score))
        score += self.scorePairs(cardsInHand,turnCard)
        #print("\tScore after pairs:    {}".format(score))
        score += self.scoreFlush(cardsInHand,turnCard)
        #print("\tScore after flush:    {}".format(score))
        score += self.scoreStraight(cardsInHand,turnCard)
        #print("\tScore after straight: {}".format(score))
        score += self.scoreKnobs(cardsInHand,turnCard)
        #print("\tScore after knobs:    {}".format(score))

        if self.useCacheLarge and (len(allCards) == 5):
            self.scores.itemset(*allCards,score)
        elif self.useCacheLarge and (len(allCards) == 4):
            self.scores_4card.itemset(*allCards,score)
        return score
        
    def score15s(self,cardsInHand,turnCard):
        '''
        Count the unique sets of cards that add to 15
        There are 5 (or 4 if turnCard is None) cards availble to make sets from, and it takes at least 2 cards
            to get to 15, so pad the combinations with 3 zeros to allow 2 cards to combine
            as well as all 5 cards to combine to score 15
        Inputs:
            * cardsInHand: list of ints of the card ids in the players hand
            * turnCad: int or None. 
                * if int is the cardid of the turn card
                * If scoring just the cards in the players hand, the turn card is None
        Returns:
            * int, the score for the hand
        '''
        values = [cardIdToCountValue[card] for card in cardsInHand]
        if turnCard is not None: #enable scoring of just cards in hand
            values.append(cardIdToCountValue[turnCard])
        values = sorted(values)
        score = 0

        if self.useCache15 and (len(values) == 5):
            if self.scores_15s.item(*values) != -1: # score in cache
                return self.scores_15s.item(*values)
        elif self.useCache15 and (len(values) == 4):
            if self.scores_15s_4card.item(*values) != -1: # score in cache
                return self.scores_15s_4card.item(*values)

        for cardsUsed in range(2,len(values)+1):
            for item in combinations(values,cardsUsed):
                total = sum(item)
                if total == 15:
                    score += 2

        if self.useCache15 and len(values) == 5:
            self.scores_15s.itemset(*values,score)
        elif self.useCache15 and  len(values) == 4:
            self.scores_15s_4card.itemset(*values,score)
        return score

    def scorePairs(self,cardsInHand,turnCard):
        '''
        Go through the cards and compute the score for pairs

        Inputs:
            * cardsInHand: list of ints of the card ids in the players hand
            * turnCad: int or None. 
                * if int is the cardid of the turn card
                * If scoring just the cards in the players hand, the turn card is None
        Returns:
            * int, the score for the hand
        '''

        values = [cardIdToFaceValue[card] for card in cardsInHand]
        if turnCard is not None: #enable scoring of just cards in hand
            values.append(cardIdToFaceValue[turnCard])
        values = sorted(values)
        score = 0

        if self.useCachePair and (len(values) == 5):
            if self.scores_pairs.item(*values) != -1:
                return self.scores_pairs.item(*values)
        elif self.useCachePair and (len(values) == 4):
            if self.scores_pairs_4card.item(*values) != -1:
                return self.scores_pairs_4card.item(*values)

        # not possible to have startIdx == idx and not possible to have 5 of a kind
        scoreForMatchCount = [0,0,2,6,12,None] 
        score = 0
        previousValue = -1
        startIdx = -1
        for idx,value in enumerate(values):
            if value == previousValue:
                continue
            else:
                matchCount = idx-startIdx
                score += scoreForMatchCount[matchCount]
                startIdx = idx
                previousValue = value
        matchCount = idx - startIdx + 1
        score += scoreForMatchCount[matchCount]

        if self.useCachePair and (len(values) == 5):
            self.scores_pairs.itemset(*values,score)
        elif self.useCachePair and (len(values) == 4):
            self.scores_pairs_4card.itemset(*values,score)
        
        return score
    
    def scoreKnobs(self,cardsInHand,turnCard):
        '''
        Score 2 points if the player has the jack that matches the suite
            of the turn card

        Inputs:
            * cardsInHand: list of ints of the card ids in the players hand
            * turnCad: int or None. 
                * if int is the cardid of the turn card
                * If scoring just the cards in the players hand, the turn card is None
        Returns:
            * int, the score for the han
        '''
        if turnCard == None: # enable scoring before turn
            return 0
        # Go over hand and see if the hand has a jack that matches the suite of the turn        
        for idx, card in enumerate(cardsInHand):
            if cardIdToFaceValue[card] is 11: # is a jack
                if cardIdToSuite[cardsInHand[idx]] == cardIdToSuite[turnCard]: # jack suite matches turn
                    return 1
        return 0

    def scoreFlush(self,cardsInHand,turnCard):
        '''
        A flush is when all 4 cards in the hand are the same suite
        An additional point for when the turn card is also of the same suite
        
        Inputs:
            * cardsInHand: list of ints of the card ids in the players hand
            * turnCad: int or None. 
                * if int is the cardid of the turn card
                * If scoring just the cards in the players hand, the turn card is None
        Returns:
            * int, the score for the hand
        '''

        values = [cardIdToSuite[card] for card in cardsInHand]
        if turnCard is not None: #enable scoring of just cards in hand
            valueTurnCard = cardIdToSuite[turnCard]
        else:
            valueTurnCard = -1 # not possible value

        score = 4
        for idx in range(len(values)-1):
            if values[idx] == values[idx+1]:
                continue
            else:
                score = 0 # break the flush, set score to 0
                break
        if (score == 4) and (valueTurnCard == values[0]):
            score += 1 # suite of turn matches suite of hand, so add a point
        return score

    def scoreStraight(self,cardsInHand,turnCard):
        '''
        Straight is 3 or more multiples in a row

        Start by looking for the longest runs.
        After completing looking for a run of a specific length, if any were found stop searching
            because searching for a run of 4 in a hand that has a run of 5, will find 2 runs of 4
            Likewise it would find 3 runs of 3. However if a run of 3 or 4 exists, want to search
            the rest of the combinations of a specific run length to find double runs
        Inputs:
            * cardsInHand: list of ints of the card ids in the players hand
            * turnCad: int or None. 
                * if int is the cardid of the turn card
                * If scoring just the cards in the players hand, the turn card is None
        Returns:
            * int, the score for the hand
        '''
        values = [cardIdToFaceValue[card] for card in cardsInHand]
        if turnCard is not None: #enable scoring of just cards in hand
            values.append(cardIdToFaceValue[turnCard])
        values = sorted(values)
        score = 0

        if self.useCacheStraight and (len(values) == 5):
            if self.scores_straight.item(*values) != -1:
                return self.scores_straight.item(*values)
        elif self.useCacheStraight and (len(values) == 4):
            if self.scores_straight_4card.item(*values) != -1:
                return self.scores_straight_4card.item(*values)

        foundRun = False
        for runLength in range(len(values),2,-1):
            for subset in combinations(values,runLength):
                for idx in range(runLength-1):
                    if (subset[idx] + 1) != (subset[idx+1]):
                        break
                else:
                    foundRun = True
                    score += runLength
            if foundRun:
                break
        if self.useCacheStraight and (len(values) == 5):
            self.scores_straight.itemset(*values,score)
        elif self.useCacheStraight and (len(values) == 4):
            self.scores_straight_4card.itemset(*values,score)
        
        return score

    def potentialScoreMap(self,hand):
        '''
        Score the possible outcomes of a raw hand (ie the 6 cards before the turn card is selected)
        Iterates over all possible turn card and card drop combinations and scores each one

        Returns an np.array of shape (6,6,52) with dtype np.float32 where
            * first index is id in the hand of the first card added to the crib
            * second index is id in the hand of the second card added to the crib
            * Third index is the possible turn card
            * Value at these indicies is the score for the resulting hand
        
        So if hand (with card ids) [1,3,4,5,6,0], the score at (0,1,9) is the score of the hand
            where handIdx cards 0 and 1 are dropped (card ids 1,3) and a turn cardId of 9
            Referencing result[0,1:] is all the possible outcomes of the hand. 
            Locations where the result is not posible (ex index (0,1,4) which has a turn card that
                is in the hand, or (0,0,9)) will have a value of np.NaN
        '''
        result = np.zeros((5,6,52),dtype=np.float32) # cannot have option 5,5 so just ignore it all together. 
        result[:] = np.NaN
        for ii in range(6):
            for jj in range(ii+1,6):
                keptHand = hand.copy()
                keptHand.pop(jj)# jj will always be > ii
                keptHand.pop(ii)
                #s = "\t"
                #for card in keptHand:
                #    s += "{:2}{}".format(cardIdToName[card],cardIdToSuite[card])
                #print(s)

                for turn in range(52):
                    if turn in hand:
                        continue # cant turn a card that is in the hand
                    result[ii,jj,turn] = self(keptHand,turn)
                    #print("\t\tTurn: {:2} {} Projected Score: {}".format(cardIdToName[turn],cardIdToSuite[turn],result[ii,jj,turn]))
        return result

    def potentialScoreStats(self,hand,topK=3,returnScoreMap=False):
        '''
        Takes in the raw 6 card hand (before cards are added to crib) and returns a dictonary
            listing the best drop cards for various stats

        Returns:
            * Dictonary with keys:
                * maxScore: [[dropCardIdx,dropCardIdx,score],...<repeats for topK scores>...]
                * expectedScore: [[dropCardIdx,dropCardIdx, average of all the possible scores],...<repeats for topK averages scores>...]
                * scoreMap: if returnScoreMap then is the result of self.potentialScoreMap(), otherwise None
        '''
        result = {'maxScore':[],
                    'expectedScore':[],
                    'scoreMap':None,
                    }
        
        scoreMap = self.potentialScoreMap(hand)
        scores = np.ma.masked_invalid(scoreMap)

        maxScores = scores.max(axis=-1)
        minScores = scores.min(axis=-1)
        expected = scores.mean(axis=-1)
        std = np.std(scores,axis=-1)
        maxExpected = expected + std
        minExpected = expected - std

        print("maxScores:")
        print(maxScores.astype(np.int32))
        #print("\nexpected:")
        #print(expected.astype(np.int32))
        #print("\nmaxnExpected:")
        #print(maxExpected.astype(np.int32))
        #print("\nminExpected:")
        #print(minExpected.astype(np.int32))
        # Want to return the worst performing cards, soo findMax=False
        result['maxScores'] = self._getMax(maxScores,topK,findMax=False)
        result['minScores'] = self._getMax(minScores,topK,findMax=False)
        result['expected'] = self._getMax(expected,topK,findMax=False)
        result['maxExpected'] = self._getMax(maxExpected,topK,findMax=True)
        result['minExpected'] = self._getMax(minExpected,topK,findMax=True)
        if returnScoreMap:
            result['scoreMap'] = scores

        print("maxScores: {}".format(result['maxScores']))

        return result

    def _getMax(self,data,topK,findMax=True):
        '''
        Returns a list of lists containing the card in hand indicies and the related score
        If findMax is True, it will return the indicies of the maxmimum values
            if it is False, it will return the indicies of the minimum values

        Takes in an nxm array
        '''

        sortedIndicies = np.unravel_index(np.argsort(data.flatten()),data.shape)
        if findMax:
            idx1 = sortedIndicies[0][-topK:][::-1]
            idx2 = sortedIndicies[1][-topK:][::-1]
        else:
            idx1 = sortedIndicies[0][:topK]
            idx2 = sortedIndicies[1][:topK]
        scores = [[ii,jj,data[ii,jj]] for ii,jj in zip(idx1,idx2)]
        return scores

    def scorePossible4CardHand(self,hand):
        '''
        Given the 6 cards the player is dealt, return a map with the resulting 4 card
            hand scores where the indicies indicate the dropped cards
        '''

        scoreMap  = np.zeros((5,6),dtype=np.float32) # cannot have option 5,5 so just ignore it all together. 
        scoreMap[:] = np.NaN
        for ii in range(6):
            for jj in range(ii+1,6):
                keptHand = hand.copy()
                keptHand.pop(jj)# jj will always be > ii
                keptHand.pop(ii)
                scoreMap[ii,jj] = self(keptHand,None)

        scoreMap = np.ma.masked_invalid(scoreMap)
        sortedIdxsFlat = np.argsort(scoreMap.flatten())[:-15] # last 15 will always be masked off as np.NaN
        sortedIdxs = np.unravel_index(sortedIdxsFlat,scoreMap.shape)
        
        dropForBestHand = [sortedIdxs[0][-1],sortedIdxs[1][-1],scoreMap[sortedIdxs[0][-1],sortedIdxs[1][-1]]]
        result = {"dropForBestHand":dropForBestHand,
                    "scoreMap":scoreMap}

        return result

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

class Game:
    '''
    Defines an entire game of cribbage
    '''
    def __init__(self,player1Type,
                        player2Type,
                        player1Name="Player1",
                        player2Name="Player2",
                        scorer=None):
        '''
        player<1,2>Type is the type of player, options are:
            * 'random'
            * 'HighestAverageHandPlayer'
        scorer: Instance of a Scorer class. Can pass in one so the cache is primed
        '''
        if player1Type.lower() == "random":
            self.player1 = RandomPlayer(name=player1Name)
        #elif player1Type.lower() == 'highestaveragehandplayer':
        #    self.player1 = HighestAverageHandPlayer(name=player1Name)
        elif player1Type.lower() == 'best4cardhandplayer':
            self.player1 = Best4CardHandPlayer(name=player1Name)
        else:
            raise ValueError("Invalid player type {} for player1".format(player1Type))
        
        if player2Type.lower() == "random":
            self.player2 = RandomPlayer(name=player2Name)
        #elif player2Type.lower() == 'highestaveragehandplayer':
        #    self.player2 = HighestAverageHandPlayer(name=player2Name)
        elif player2Type.lower() == 'best4cardhandplayer':
            self.player2 = Best4CardHandPlayer(name=player2Name)
        else:
            raise ValueError("Invalid player type {} for player2".format(player1Type))

        if type(scorer) is HandScorer:
            self.handScorer = scorer
        elif type(scorer) is str: 
            # check the testing case, prevents from allocating/deallocating 100's of MB of RAM
            #   when running tests
            # As of 20200608, using this takes test time from 2.5s to 1.7s
            if scorer.lower() == "do-not-create":
                self.handScorer = None
            else:
                self.handScorer = HandScorer()
        else:
            self.handScorer = HandScorer()

        self.deck = Deck()

        self.player1Score = 0
        self.player2Score = 0

        # Flag to control who deals. True means player 1, False means player 2
        # Is inverted at the start of self.playHand()
        self.player1Dealer = False 

        # Flag for signaling the end of the game.
        # This is set by calling self._checkGameOver()
        self.gameOver = False

    def playGame(self):
        '''
        Play through an entire game of cribbage
        '''
        try:
            while not self.gameOver:
                self.deck.shuffle()
                self.playHand()
                #print("{} to {}".format(self.player1Score, self.player2Score))
        except KeyboardInterrupt:
            print("\nExiting the game!")
        except EndOfGameException as e:
            print(e.message)
        except Exception:
            import traceback
            info = sys.exc_info()
            print("Unexpected error:", info[0])
            print(info[1])
            traceback.print_tb(info[2])

    def playHand(self):
        '''
        Play through a single hand
        ''' 
        self._resetHands()
        self.player1Dealer = not self.player1Dealer
        
        self._deal()
        #print("player1 hand: {}".format(self.player1.hand))
        #print("player2 hand: {}".format(self.player2.hand))

        while len(self.cardsPlayed) < 8 and not self.gameOver:
            self.player1Turn = not self.player1Turn # invert so the next player goes
            if self.player1Turn:
                cardPlayed = self.player1.playCard(self.cardsPlayed,
                                                self.cardTotal,
                                                self.cardsSinceReset)
            else:
                cardPlayed = self.player2.playCard(self.cardsPlayed,
                                                self.cardTotal,
                                                self.cardsSinceReset)
            # run the checks for scoring and reseting the game stated based on a go
            # Then if None card was played, go to the next iterations
            self._checkGo(cardPlayed)
            if cardPlayed is None:
                continue
            # Error checking of the card the player laid
            if cardIdToCountValue[cardPlayed] + self.cardTotal > 31:
                raise ValueError("Invalid card was returned, score is over 31 "+\
                    "when player {} laid card {}".format(self.player1.name if self.player1Turn else self.player2.name,cardPlayed)+\
                    "which brought total from {} to {}".format(self.cardTotal,self.cardTotal+cardIdToCountValue[cardPlayed]))

            self.cardsPlayed.append(cardPlayed)
            self.cardTotal += cardIdToCountValue[cardPlayed]
            self.cardsSinceReset += 1

            score = self._scorePegging()
            self.player1Score += score if self.player1Turn else 0
            self.player2Score += score if not self.player1Turn else 0
            self._checkGameOver()
        
        # point for last
        self.player1Score += 1 if self.player1Turn else 0
        self.player2Score += 1 if not self.player1Turn else 0

        # Count the hands
        # Dealer always counts first
        
        if self.player1Dealer:
            #player1StartingScore = self.player1Score # debugging use only
            self.player1Score += self.handScorer(self.player1.hand, self.turnCard)
            self._checkGameOver()
            self.player2Score += self.handScorer(self.player2.hand, self.turnCard)
            self._checkGameOver()
            self.player1Score += self.handScorer(self.player1.crib, self.turnCard)
            self._checkGameOver()
        else:
            #player1StartingScore = self.player1Score #debugging use only
            self.player2Score += self.handScorer(self.player2.hand, self.turnCard)
            self._checkGameOver()
            self.player1Score += self.handScorer(self.player1.hand, self.turnCard)
            self._checkGameOver()
            self.player2Score += self.handScorer(self.player2.crib, self.turnCard)
            self._checkGameOver()

        '''
        # Useful for debugging players
        scored = self.player1Score-player1StartingScore
        print("\tPlayer 1 expected {} scored {}".format(self.player1.predictedScore,scored))
        if self.player1.predictedScore > scored:
            print("Original hand: {}\n\tcardIds: {}".format(printCards(self.player1.originalDealtHand),self.player1.originalDealtHand))
            print("Hand Ids: {} Turn Id: {}".format(self.player1.hand,self.turnCard))
            
            print("Scorer output from when hand was chosen")
            for key in self.player1._scorer_output:
                print("{}\n{}".format(key,self.player1._scorer_output[key]))
            print("")
            raise ValueError("\nExpected minimum score of {}, scored {}\n".format(self.player1.predictedScore,scored) + \
                "Hand: {} Turn {}\n\n".format(printCards(self.player1.hand),printCards([self.turnCard])))
        '''

    def _resetHands(self):
        '''
        reset all game logic that starts over every hand
        '''
        self.player1.resetHands()
        self.player2.resetHands()

        self.cardsPlayed = [] # cardIds of all the cards shown, in order of play
        self.cardsSinceReset = 0 # the number of cards since 31 or since game reset from a 'go'
        self.cardTotal = 0 # current total of the cards
        self.go_lastPlayWasGo = False # flag for checking of rest by 'gos'
        self.go_inGoState = False # flag for checking if the game is in a state of 'go'
       
    def _checkGameOver(self):
        '''
        Determine if a player has won and set the gameOver flag
        '''
        if (self.player1Score >= 121):
            self.gameOver = True
            raise EndOfGameException(self.player1.name,
                                    self.player1Score,
                                    self.player2.name,
                                    self.player2Score)
        elif (self.player2Score >= 121):
            self.gameOver = True
            raise EndOfGameException(self.player2.name,
                                    self.player2Score,
                                    self.player1.name,
                                    self.player1Score)

    def _deal(self):
        '''
        Deal the cards to each player and build the crib
        Score points for 'His Heels' if a Jack is turned

        Sets the turn card value
        '''
        player1Crib = self.player1.deal(self.deck,self.player1Dealer,self.handScorer)
        player2Crib = self.player2.deal(self.deck,not self.player1Dealer,self.handScorer)

        self.turnCard = self.deck.getCards(1)[0]

        if self.player1Dealer:
            self.player1.recieveCardsForCrib(player2Crib)
            self.player1Score += 2 if cardIdToFaceValue[self.turnCard] == 11 else 0
            self.player1Turn = False # looks backwards, but first thing game loop does is invert the player turn
        elif not self.player1Dealer:
            self.player2.recieveCardsForCrib(player1Crib)
            self.player2Score += 2 if cardIdToFaceValue[self.turnCard] == 11 else 0
            self.player1Turn = True # looks backwards, but first thing game loop does is invert the player turn
        else:
            raise ValueError("Neither player1 or player2 is the dealer!")

        # Points can be scored on the deal, so it is possible to win in this function
        self._checkGameOver()

    def _checkGo(self,cardPlayed):
        '''
        When a player is unable to lay a card because it would cause the total to 
            go over 31, they call a 'Go'. This means the other player has the chance
            to keep playing upto 31. They must continue to play until they are unable
            to play any more cards. They can continue to score pairs, straights, 15s and 31s
        The one tricky part is the person who can still play gets 1 point at the start of the
            Go process, but not for every subsequent one. Ex:
                cardTotal is 22 (player 1 only has cards worth 10 in hand so cannot lay)
                player 1 calls 'Go', and player 2 scores 1 point
                player 2 lays  4,4 bringing the total to 30 and they are out of cards
                Player2 scores a total of 1 point for the go plus 2 for the pair
                    giving them 3 points.
            So to track this, need 2 state variables:
                1) Was the last players turn a go?
                    * if it is and this players turn is a go, neither can lay cards and reset
                2) Is the game in a 'go state' where one player cannot go, but the oher can
                    need to track so they can keep laying cards without scoring a point every time
        '''
        if cardPlayed is not None:
            self.go_lastPlayWasGo = False
            return
        elif (cardPlayed is None) and self.go_lastPlayWasGo: 
            # both players are in a go, so reset the game state and go to next hand
            self.cardsSinceReset = 0
            self.cardTotal = 0
            self.go_lastPlayWasGo = False
            self.go_inGoState = False
            return
        elif cardPlayed is None:
            # See if someone gets a point for the go
            # Then go to the next hand
            if not self.go_inGoState:
                # when entering a go state, the other player gets a point
                self.player1Score += 1 if not self.player1Turn else 0
                self.player2Score += 1 if self.player1Turn else 0
            self.go_lastPlayWasGo = True
            self.go_inGoState = True
            return
            
    def _scorePegging(self):
        '''
        Return the score for the last card played 
        '''
        score = 0

        faceValues = [cardIdToFaceValue[card] for card in self.cardsPlayed]
        faceValues = faceValues[::-1] # reverse order to make searching logic easier
        
        # count the pairs that are on the table. Must be in order played
        # Need at least 2 cards to have a pair
        if self.cardsSinceReset >= 2:
            pairCount = 0
            for idx in range(self.cardsSinceReset-1):
                if faceValues[idx] == faceValues[idx+1]:
                    pairCount += 1
                else:
                    break
            score += [0,2,6,12][pairCount]

        # Score a run on the table, must be in increasing order
        # Need at least 3 cards for a run
        if self.cardsSinceReset >= 3:
            runCount = 1
            for idx in range(self.cardsSinceReset-1):
                if faceValues[idx] == (faceValues[idx+1] + 1):
                    runCount += 1
                else:
                    break
            score += [0,0,0,3,4,5,6,7,8][runCount]

        # 31 must be counted after runs and pairs as it resets cardsSinceReset
        if self.cardTotal == 15:
            score += 2
        elif self.cardTotal == 31:
            score += 2
            self.cardTotal = 0
            self.cardsSinceReset = 0
        
        return score
        









