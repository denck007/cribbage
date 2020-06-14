
import sys

from Cribbage import HandScorer, Deck
from Cribbage.Exceptions import EndOfGameException
from Cribbage.Players import RandomPlayer, Best4CardHandPlayer,BestMinimalScorePlayer
from Cribbage.cribbage import cardIdToCountValue,cardIdToFaceValue, cardIdToSuiteName

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
        elif player1Type.lower() == 'bestminimalscoreplayer':
            self.player1 = BestMinimalScorePlayer(name=player1Name)
        elif player1Type.lower() == 'best4cardhandplayer':
            self.player1 = Best4CardHandPlayer(name=player1Name)
        else:
            raise ValueError("Invalid player type {} for player1".format(player1Type))
        
        if player2Type.lower() == "random":
            self.player2 = RandomPlayer(name=player2Name)
        elif player2Type.lower() == 'bestminimalscoreplayer':
            self.player2 = BestMinimalScorePlayer(name=player2Name)
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

        self.deck = Deck.Deck()

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