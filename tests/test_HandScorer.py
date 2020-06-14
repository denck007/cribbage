from unittest import TestCase
from Cribbage.cribbage import HandScorer, cardIdToFaceValue
import numpy as np

class test_HandScorer(TestCase):

    def test_Cache(self):
        '''
        Verify that items are cached in the correct location
        '''
        scorer = HandScorer()
        score = scorer([0,1,2,3],4) # verify order independent
        self.assertEqual(score,12)
        self.assertEqual(scorer.scores_15s[1,2,3,4,5],2) # uses count value as idx
        self.assertEqual(scorer.scores_pairs[1,2,3,4,5],0) # uses face value as idx
        self.assertEqual(scorer.scores_straight[1,2,3,4,5],5) # uses face value as idx

        score = scorer([0,1,2,3],None) # verify order independent
        self.assertEqual(score,8)
        self.assertEqual(scorer.scores_15s_4card[1,2,3,4],0) # uses count value as idx
        self.assertEqual(scorer.scores_pairs_4card[1,2,3,4],0) # uses face value as idx
        self.assertEqual(scorer.scores_straight_4card[1,2,3,4],4) # uses face value as idx


    def test_scoreFlush(self):
        '''
        Test cases for flush
        '''
        scorer = HandScorer()
        # [[cards in hand], turn card, score]
        cases = [[[0,1,2,3],4,5],
                [[0,1,2,3],51,4],
                [[0,1,2,51],4,0],
                [[0,1,2,3],None,4],
                [[0,1,2,50],None,0]]
            
        for case in cases:
            cardsInHand,turn,scoreCorrect = case
            score = scorer.scoreFlush(cardsInHand,turn)
            self.assertEqual(score,scoreCorrect,msg="predicted {} correct {} with hand {} and turn {}".format(score,scoreCorrect,cardsInHand,turn))

    def test_score15s(self):
        '''
        Test the calculation of the score for cards totaling 15
        '''
        scorer = HandScorer()
        # each row is [[cardsInHand],turnCard,score]
        cases = [[[0,1,2,3],4,2],   # A, 2, 3, 4, 5 = 15x2
                [[0,4,9,10],11,6],  # A, 5,10, J, Q = 15x6
                [[5,8,5+13,8+2*13],0,8],    # 6, 9, 6, 9, A = 15x8  
                [[5,7+3*13,3+13,3+2*13],0,4],  # 6,8,4,4,A = 15x4 
                [[4,9,10,11],None,6], #5,10 + 5,J + 5,Q + 5,K 
                ]

        for case in cases:
            cardsInHand,turn,scoreCorrect = case
            score = scorer.score15s(cardsInHand,turn)
            self.assertEqual(score,scoreCorrect)

    def test_scoreKnobs(self):

        scorer = HandScorer()

        # each row is [[cardsInHand],turnCard,score]
        cases = [[[0,1,2,3,4,5],6,0],
                [[0,1,2,3,10],1,1], # has jack, suite matches
                [[0,1,2,3,10+13*3],4,0], # has jack, suit does not match
                [[0,10+13*2,2,3,1],3+13*2,1], # has jack does match
                [[0,1,2,3,4],10,0], # is his heels, no points 
                [[0,3,3,5],None,0], # not possible to calculate without turn
                ]

        for case in cases:
            hand, turn, scoreCorrect = case
            score = scorer.scoreKnobs(hand,turn)
            self.assertEqual(score,scoreCorrect)
        
    def test_scorePairs(self):

        scorer = HandScorer()

        # each row is [[cards in hand],turn, score]
        cases = [[[0,1,2,3],4,0], # A, 2, 3, 4, 5 - No pairs
                [[0,13,26,39],1,12],   # A, A, A, A, 2 - 4 of a kind
                [[1,0,13,26],39,12],  # 2, A, A, A, A - 4 of a kind, checks that sorting works
                [[0,2,2+13,2+13*2],2+13*3,12], # A, 3, 3, 3, 3 # 4 of a kind, check when last card matches previous
                [[1,2,3,3],4,2], # 2,3,4,4,5 -1 pair
                [[1,1,2,10],10,4], # 2,2,3,J,J - 2 pairs of 2
                [[9,10,11,12],0,0], # 10,J,Q,K,A - no pairs - checks that  it uses face values
                [[15,15+13,15+13*2,22],22+13,8], # 3,3,3,10,10 - 3 of a kind and a pair
                [[0,2,2+13,3],None,2], # 3,3 - pair for 2
                [[2,2+13,2+13*2,3],None,6], # 3,3,3,4 - 3 of a kind for 6
                ]

        for case in cases:
            cardsInHand,turn,scoreCorrect = case
            score = scorer.scorePairs(cardsInHand,turn)
            self.assertEqual(score,scoreCorrect, "predicted {} Correct: {} for hand {} with turn {}".format(score,scoreCorrect,cardsInHand,turn))

    def test_scoreStraight(self):

        scorer = HandScorer()

        # each row is [[cards in hand],turn, score]
        cases = [[[0,1,2,3],4,5], # A, 2, 3, 4, 5 - 5 card straight
                [[0,13,1,2],5,6], # A, A, 2,3, 6 - 2x 3 card straights for 6
                [[9,27,29,23],24,3], # 10, 2, 4, J, Q - run of 3
                [[9,10,11,12],None,4], # 10, J, Q, K - run of 4
                [[0,2,4,6],None,0] # no points
                ]

        for case in cases:
            cardsInHand,turn,scoreCorrect = case
            score = scorer.scoreStraight(cardsInHand,turn)
            self.assertEqual(score,scoreCorrect)

    def test_scorer(self):
        '''
        Test scoring of all the functions together
        '''
        scorer = HandScorer()

        # Each row is [[cardsInHand], turn, score]
        cases = [
            [[0,1,2,3],4,12], # 15-2 5flush, 5straight
            [[8,10,11+13*3,12],36,8], # pair of Q, 2x straight JQK, heels but it doesn't get counted here
            [[8,9,10,11],12,11], # test_Game.test_playHand, Hand #1, player 1 hand
            [[4,5,6,7],12,13], # test_Game.test_playHand, Hand #1, player 2 hand
            [[0,1,2,3],12,13], # test_Game.test_playHand, Hand #1, player 1 crib
            [[2,9,18,3],23,0], # test_Game.test_playHand, Hand #2, player 1 hand
            [[1,10,5,4],23,10], # test_Game.test_playHand, Hand #2, player 2 hand
            [[12,24,9,0],23,4],# test_Game.test_playHand, Hand #2, player 2 crib
        ]

        for case in cases:
            
            cardsInHand,turn,scoreCorrect = case
            
            score = scorer(cardsInHand,turn)
            self.assertEqual(score,scoreCorrect)

    def test_potentialScoreMap(self):
        '''

        '''

        scorer = HandScorer()
        # hand of A, 2, 4, 6 ( drop idx 2,4)
        # Best turn would be a 3 for a score of 10:
        #    15-2 (2,3,4,6), straight (A,2,3,4) for 6, flush (A,2,4,6) for 10
        hand = [0,1,2,3,4,5] # A, 2, 3, 4, 5, 6
        result = scorer.potentialScoreMap(hand)
        self.assertTrue(np.isnan(result[2,4,2])) # card is in hand, so should be NaN
        self.assertEqual(result[2,4,2+13*1],10) # all other versions should be 10
        self.assertEqual(result[2,4,2+13*2],10)
        self.assertEqual(result[2,4,2+13*3],10)

