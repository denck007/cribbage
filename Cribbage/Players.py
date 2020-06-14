from Cribbage.cribbage import cardIdToCountValue

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
