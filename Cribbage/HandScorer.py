from Cribbage.cribbage import cardIdToCountValue,cardIdToFaceValue,cardIdToName,cardIdToSuite,cardIdToSuiteName
import numpy as np
from itertools import combinations

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

    def scorePossible5CardHand(self,hand):
        '''
        Given the 6 cards the player is dealt, return a map with the resulting 4 card hand scores
            where the first 2 indicies indicate the dropped cards and the 3rd references the
            possible turn card
        ''' 
        scoreMap  = np.zeros((5,6,52),dtype=np.float32) # cannot have option 5,5 so just ignore it all together. 
        scoreMap[:] = np.NaN
        for ii in range(6):
            for jj in range(ii+1,6):
                keptHand = hand.copy()
                keptHand.pop(jj)# jj will always be > ii
                keptHand.pop(ii)
                for turnCardId in range(52):
                    if turnCardId in hand:
                        continue
                    scoreMap[ii,jj,turnCardId] = self(keptHand,turnCardId)

        scoreMap = np.ma.masked_invalid(scoreMap)
        mins = scoreMap.min(axis=-1)
        maxs = scoreMap.max(axis=-1)
        sortedIdxsFlat = np.argsort(mins.flatten())[:-15] # last 15 will always be masked off as np.NaN
        sortedIdxs = np.unravel_index(sortedIdxsFlat,mins.shape)

        dropForBestHand = [sortedIdxs[0][-1],sortedIdxs[1][-1],scoreMap[sortedIdxs[0][-1],sortedIdxs[1][-1]]]
        result = {"dropForBestHand":dropForBestHand,
                    "mins":mins,
                    "maxs":maxs,
                    "scoreMap":scoreMap}
        return result

    def scorePossibleCribHands(self,hand):
        '''
        Given a 6 card hand, find the scores of the possible crib hands
        Does not count the turn card in with the crib
        '''
        scoreMap  = np.zeros((5,6,52,52),dtype=np.float32) # cannot have option 5,5 so just ignore it all together. 
        scoreMap[:] = np.NaN
        for ii in range(6):
            for jj in range(ii+1,6):
                keptHand = hand.copy()
                toCrib = []
                toCrib.append(keptHand.pop(jj))# jj will always be > ii
                toCrib.append(keptHand.pop(ii))
                for cribCard1Id in range(52):
                    if cribCard1Id in hand:
                        continue
                    for cribCard2Id in range(cribCard1Id+1,52):
                        if cribCard2Id in hand:
                            continue
                        scoreMap[ii,jj,cribCard1Id,cribCard2Id] = self(toCrib + [cribCard1Id,cribCard2Id],None)

        scoreMap = np.ma.masked_invalid(scoreMap)
        mins = scoreMap.min(axis=(-2,-1))
        maxs = scoreMap.max(axis=(-2,-1))

        sortedIdxsFlat = np.argsort(mins.flatten())[:-15] # last 15 will always be masked off as np.NaN
        sortedIdxs = np.unravel_index(sortedIdxsFlat,mins.shape)

        result = {"mins":mins,
                    "maxs":maxs,
                    "scoreMap":scoreMap}

        return result






