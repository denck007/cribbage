from unittest import TestCase
from Cribbage import Game
from Cribbage.Exceptions import EndOfGameException
from Cribbage.cribbage import cardIdToFaceValue

class test_Game(TestCase):
    '''

    '''

    def test__checkGameOver(self):
        '''
        Verify that either player at or over 121 sets gameOver flag
        '''
        game = Game("random","random","do-not-create")

        cases = [[100,121,True],
                [121,0,True],
                [130,100,True],
                [43,140,True],
                [120,120,False]]
            
        for case in cases:
            game.gameOver = False
            game.player1Score, game.player2Score, gameOverCorrect = case
            if gameOverCorrect:
                self.assertRaises(EndOfGameException,game._checkGameOver)
            else:
                game._checkGameOver()
            self.assertEqual(game.gameOver,gameOverCorrect)

    def test__deal(self):
        '''
        test that cards are dealt out correctly
        '''
        # Player 1 gets hand [8,9,10,11] and puts [4,5] in crib
        # Player 2 get hand [0,1,2,3] and puts [6,7] in crib
        # Player 1 gets crib
        # turn is 12
        # no points are given out
        game = Game("random","random",scorer="do-not-create") # not counting hands, so do not create a scorer
        game.player1Dealer = True
        game.deck.cards = [12,6,7,0,1,2,3,4,5,8,9,10,11] 
        game._deal()
        self.assertEqual(game.player1Score,0)
        self.assertEqual(game.player2Score,0)
        self.assertEqual(sorted(game.player1.hand),[8,9,10,11])
        self.assertEqual(sorted(game.player2.hand),[0,1,2,3])
        self.assertEqual(sorted(game.player1.crib),[4,5,6,7])
        self.assertIsNone(game.player2.crib)

        # Player 1 gets hand [8,9,10,11] and puts [4,5] in crib
        # Player 2 get hand [0,1,2,3] and puts [6,7] in crib
        # Player 2 gets crib
        # turn is 23 (Jack)
        # Player gets 2 for His Heels
        game = Game("random","random",scorer="do-not-create") # not counting hands, so do not create a scorer
        game.player1Dealer = False
        game.deck.cards = [23,6,7,0,1,2,3,4,5,8,9,10,11] 
        game._deal()
        self.assertEqual(game.player1Score,0)
        self.assertEqual(game.player2Score,2)
        self.assertEqual(sorted(game.player1.hand),[8,9,10,11])
        self.assertEqual(sorted(game.player2.hand),[0,1,2,3])
        self.assertIsNone(game.player1.crib)
        self.assertEqual(sorted(game.player2.crib),[4,5,6,7])

    
    def test__scorePegging(self):
        '''
        Test cases for the score when a player lays down cards
        '''

        game = Game("random","random",scorer="do-not-create") # not counting hands, so do not create a scorer

        # each row is [[cardsPlayed],cardsSinceReset,score]
        cases = [
            [[0],1,0], # only 1 card has been played, no points scored
            [[0,13],2,2], # 2 cards played, have a pair for 2
            [[0,1,2],3,3], # 3 card run, all cards in play
            [[0,1,3,4],4,0], # all cards in play, no pairs or straights
            [[0,1,2,3,3+13],3,2], # pair of 3,3+13, no straight
            [[0,1,2,3,4],3,3], # run of 2,3,4. Cards 0 and 1 are not included because of cardsSinceReset
            [[0,1,3,0],2,0], # pair, but not in cardsSinceReset
        ]

        for case in cases:
            game.cardsPlayed,game.cardsSinceReset, scoreCorrect = case
            game.cardTotal = sum(game.cardsPlayed[::-1][:game.cardsSinceReset])
            score = game._scorePegging() 
            self.assertEqual(score,scoreCorrect)

    def test__checkGo(self):
        '''
        Check all the logic around the checkGo function
        '''
        # each row is [cardPlayed,cardsSinceReset,cardTotal,lastPlayWasGo,inGoState,player1Score,player2Score]]

        # Card total is 25 [10,J,5], 3 cards since reset
        # player1 unable to lay (just layed a None)
        # player2 was able to lay previous round
        # both players have score == 0 to start
        game = Game("random","random",scorer="do-not-create") # not counting hands, so do not create a scorer
        game.cardTotal = 25
        game.cardsSinceReset = 3
        game.cardsPlayed = [9,10,4]
        game.go_lastPlayWasGo = False
        game.go_inGoState = False
        game.player1Turn = True
        
        game._checkGo(None) # player1 lays a None
        self.assertEqual(game.cardsSinceReset,3) # no change
        self.assertEqual(game.cardTotal,25) # no change
        self.assertEqual(game.go_lastPlayWasGo,True)
        self.assertEqual(game.go_inGoState,True)
        self.assertEqual(game.player1Score,0)
        self.assertEqual(game.player2Score,1)

        # now it is player2's turn and they can lay a card
        game.player1Turn = False
        game.cardsPlayed.append(0) # player 2 lays an ace
        game.cardTotal += 1
        game.cardsSinceReset += 1

        game._checkGo(0) # player 2 lays an ace
        self.assertEqual(game.cardsSinceReset,4) # no change
        self.assertEqual(game.cardTotal,26) # no change
        self.assertEqual(game.go_lastPlayWasGo,False) # changes
        self.assertEqual(game.go_inGoState,True) # still in go state
        self.assertEqual(game.player1Score,0) # no points are scored by either player
        self.assertEqual(game.player2Score,1)

        # now player 1 cannot lay (as before)
        # game is in same state as before, but with lastPlayWasGo == True
        game.player1Turn = True
        game._checkGo(None) # player1 lays a None
        self.assertEqual(game.cardsSinceReset,4) # no change
        self.assertEqual(game.cardTotal,26) # no change
        self.assertEqual(game.go_lastPlayWasGo,True) # changes
        self.assertEqual(game.go_inGoState,True) # still in go state
        self.assertEqual(game.player1Score,0) # no points are scored by either player
        self.assertEqual(game.player2Score,1)

        # finally player 2 can no longer lay any cards
        # game state resets
        game.player1Turn = False
        game._checkGo(None)
        self.assertEqual(game.cardsSinceReset,0) # resets
        self.assertEqual(game.cardTotal,0) # resets
        self.assertEqual(game.go_lastPlayWasGo,False) # resets
        self.assertEqual(game.go_inGoState,False) # resets
        self.assertEqual(game.player1Score,0) # no points are scored by either player
        self.assertEqual(game.player2Score,1)

    def test_playHand(self):
        '''
        Run through the entire hand and make sure everything works properly
        '''
        game = Game("random","random",scorer=None) # actually scoring hands, so create scorer

        # Player 1 gets hand [8,9,10,11] (values [9,10,J,Q])and puts [4,5] (values[5,6]) in crib
        # Player 2 get hand [0,1,2,3] (values[A,2,3,4]) and puts [6,7] (values[7,8]) in crib
        # Player 1 gets crib
        # turn is 12 (value K)
        # Order is: 
        #   player: p1, p2, p1, p2, p2, p2, p1, p1
        #  cardIdx:  8,  0,  9,  1,  2,  3, 10, 11
        #     card:  9,  A, 10,  2,  3,  4,  J,  Q
        #    count:  9, 10, 20, 22, 25, 29, 10, 20 
        #       go:  n,  n,  n,  n,  y,  y,  n,  y 
        #   scored:  0,  0,  0,  0,  1,  0,  0,  2* 1 for a go, 2 for last
        #  p1total:  0,  0,  0,  0,  0, 3*,  0,  2  * self layed run of 3
        #  p2total:  0,  0,  0,  0,  1,  4,  4,  4
        #
        # player 1 scores: run of 5 for 5, flush of 5 for 10, knobs for 11
        # player 2 scores: 15-2 (A+4+K), 15-4 (2+3+K), run of 4 for 8, flush of 5 for 13
        # player 1 crib scores: 15-2 (5+K), 15-4 (7+8) run of 4 for 8, flush of 5 for 13,
        game = Game("random","random")
        game.deck.cards = [12,7,6,3,2,1,0,5,4,11,10,9,8] 
        game.player1Dealer = False # playHand inverts this
        game.playHand()
        self.assertEqual(game.cardsPlayed,[8,  0,  9,  1,  2,  3, 10, 11])
        self.assertEqual(game.player1.crib,[4,5,6,7])
        self.assertEqual(game.player1Score,2+11+13)
        self.assertEqual(game.player2Score,4+13)

        # Next hand
        # Make sure that player 2 is dealer this time and gets crib
        # player 2 gets His Heels

        # Player 1 gets hand [2,9,18,3] (value[3,10, 6(diffsuite), 4]) and puts [9,0] (value[J,A]) in crib
        # Player 2 get hand [1,10,5,4] (value[2,J,6,5]) and puts [12,24] (value[K,Q]) in crib
        # Player 2 gets crib
        # turn is 23 (value J (diffSuite))
        # Order is: 
        #   player: p2, p1, p2, p1, p2, p1, p2, p1
        #  cardIdx:  1,  2,  10, 9,  5, 18,  4,  3  
        #     card:  2,  3,  J, 10,  6,  6,  5,  4
        #    count:  2,  5, 15, 25, 31,  6, 11, 15
        #       go:  n,  n,  n,  n,  n,  n,  n,  n
        #   scored:  0,  0,  2,  0,  2,  0,  0,  3* 2 for 15, last
        #  p1total:  0,  0,  0,  0,  0,  0,  0,  3
        #  p2total:  2,  2,  4,  4,  6,  6,  6,  6 Started off with 2 for HisKnees
        #
        # player 1 score:  0
        # player 2 score: 15-2 (5+J), 15-4 (5+J), pair if J for 6, flush of 4 for 10
        # player 2 crib: straight (10,J,Q,K) for 4
        game.deck.cards = [10+13, # turn
                            12,24, # p2 crib
                            4,5,10,1,
                            0, 9+13, # p1 crib
                            3, 18, 9,2, # p1 hand
                            ]  
        game.playHand()
        self.assertEqual(game.cardsPlayed,[1,  2,  10, 9,  5, 18,  4,  3  ])
        self.assertEqual(game.player1Dealer,False) # player2 is dealer
        self.assertEqual(game.player1.crib,None)
        self.assertEqual(game.player2.crib,[24,12,9+13,0])
        self.assertEqual(game.player1Score,26+3+0) # 26 from previous hand, 3 pegging, 0 hand
        self.assertEqual(game.player2Score,17+6+14) # 17 from previous hand, 6 pegging, 14 hand




