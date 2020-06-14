
from Cribbage import Game,HandScorer


if __name__ == "__main__":
    scorer = HandScorer()
    player1Wins = 0
    gamesToPlay = 10000
    for ii in range(gamesToPlay):
        #game = Game("Best4CardHandPlayer","random",scorer=scorer)
        #game = Game("BestMinimalScorePlayer","Best4CardHandPlayer",scorer=scorer)
        game = Game("Best4CardHandPlayer","random",scorer=scorer)
        #game = Game("Random","random",scorer=scorer)
        game.playGame()
        if game.player1Score > game.player2Score:
            player1Wins += 1
    print("Player 1 won {}/{} games, {:.1f}%".format(player1Wins,gamesToPlay,float(player1Wins)/gamesToPlay*100.))
