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
                                                                        